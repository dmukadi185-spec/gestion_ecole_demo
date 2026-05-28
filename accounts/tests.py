from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Classe, Eleve
from accounts.utils import normalize_identifiant

User = get_user_model()


class IdentifiantTests(TestCase):
    def test_generate_identifiant_uppercase_space_separated(self):
        self.assertEqual(
            Eleve.generate_identifiant("Dupont", "Mbuya", "Kabongo"),
            "DUPONT MBUYA KABONGO",
        )

    def test_user_save_normalizes_identifiant_to_uppercase(self):
        user = User.objects.create_user(identifiant="  eleve001  ")
        user.refresh_from_db()
        self.assertEqual(user.identifiant, "ELEVE001")

    def test_normalize_identifiant_strips_collapses_spaces_and_uppercases(self):
        self.assertEqual(normalize_identifiant("  dupont  mbuya  "), "DUPONT MBUYA")


class AuthFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.classe = Classe.objects.create(niveau="6e", departement="Scientifique")
        self.identifiant = Eleve.generate_identifiant("Kabila", "M.", "Jean")
        self.user = User.objects.create_user(identifiant=self.identifiant)
        self.user.set_password("secret123")
        self.user.password_created = True
        self.user.is_active = True
        self.user.save()
        self.eleve = Eleve.objects.create(
            user=self.user,
            nom="Kabila",
            postnom="M.",
            prenom="Jean",
            classe=self.classe,
        )

    def test_home_is_public_for_anonymous_users(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Connexion")

    def test_home_login_redirects_to_dashboard(self):
        response = self.client.post(
            reverse("home"),
            {"username": self.identifiant, "password": "secret123"},
        )
        self.assertRedirects(response, reverse("dashboard:index"))

    def test_login_accepts_lowercase_identifiant_input(self):
        response = self.client.post(
            reverse("home"),
            {"username": self.identifiant.lower(), "password": "secret123"},
        )
        self.assertRedirects(response, reverse("dashboard:index"))

    def test_authenticated_user_on_home_sees_landing_with_dashboard_link(self):
        self.client.login(username=self.identifiant, password="secret123")
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bienvenue sur la plateforme")
        self.assertContains(response, "Accéder au tableau de bord")

    def test_signin_redirects_to_dashboard(self):
        response = self.client.post(
            reverse("accounts:signin"),
            {"username": self.identifiant, "password": "secret123"},
        )
        self.assertRedirects(response, reverse("dashboard:index"))

    def test_login_rejects_user_without_eleve_profile(self):
        orphan_id = "ORPHANUSER"
        User.objects.create_user(
            identifiant=orphan_id,
            password="secret123",
            password_created=True,
            is_active=True,
        )
        response = self.client.post(
            reverse("home"),
            {"username": orphan_id, "password": "secret123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aucun profil élève")

    def test_activation_auto_logs_in_and_redirects(self):
        pending_id = Eleve.generate_identifiant("Test", "T.", "Marie")
        pending_user = User.objects.create_user(identifiant=pending_id)
        Eleve.objects.create(
            user=pending_user,
            nom="Test",
            postnom="T.",
            prenom="Marie",
            classe=self.classe,
        )
        response = self.client.post(
            reverse("accounts:activate"),
            {
                "identifiant": pending_id.lower(),
                "password": "newpass123",
                "password_confirm": "newpass123",
            },
        )
        self.assertRedirects(response, reverse("dashboard:index"))
        pending_user.refresh_from_db()
        self.assertTrue(pending_user.password_created)
        self.assertTrue(pending_user.is_active)

    def test_activation_rejects_unknown_identifiant(self):
        response = self.client.post(
            reverse("accounts:activate"),
            {
                "identifiant": "INCONNU",
                "password": "newpass123",
                "password_confirm": "newpass123",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aucun compte trouvé")

    def test_activation_rejects_user_without_eleve(self):
        orphan = User.objects.create_user(identifiant="NOPROFILE")
        response = self.client.post(
            reverse("accounts:activate"),
            {
                "identifiant": "NOPROFILE",
                "password": "newpass123",
                "password_confirm": "newpass123",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aucun profil élève")

    def test_user_without_eleve_profile_gets_friendly_page(self):
        orphan = User.objects.create_user(identifiant="ORPHAN01")
        orphan.set_password("secret123")
        orphan.password_created = True
        orphan.is_active = True
        orphan.save()
        self.client.login(username="ORPHAN01", password="secret123")
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 403)
        self.assertContains(
            response,
            "Profil élève non configuré",
            status_code=403,
        )


class SessionSettingsTests(TestCase):
    def test_session_inactivity_timeout_configured(self):
        self.assertEqual(settings.SESSION_COOKIE_AGE, 3600)
        self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)
        self.assertFalse(settings.SESSION_EXPIRE_AT_BROWSER_CLOSE)


class EleveAdminTests(TestCase):
    def test_admin_create_eleve_auto_generates_user_and_identifiant(self):
        from django.contrib.admin.sites import site
        from accounts.admin import EleveAdmin

        classe = Classe.objects.create(niveau="5e", departement="Littéraire")
        eleve = Eleve(nom="Mbuya", postnom="Kabongo", prenom="Jean", classe=classe)
        admin = EleveAdmin(Eleve, site)
        request = type("Request", (), {"user": User.objects.create_superuser("admin", "adminpass")})()

        admin.save_model(request, eleve, None, change=False)

        eleve.refresh_from_db()
        self.assertEqual(eleve.user.identifiant, "MBUYA KABONGO JEAN")
        self.assertFalse(eleve.user.password_created)
        self.assertTrue(eleve.user.is_active)

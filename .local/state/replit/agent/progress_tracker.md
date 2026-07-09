[x] 1. Install the required packages
[x] 2. Restart the workflow to see if the project is working
[x] 3. If the app uses external auth (Supabase Auth, Firebase, NextAuth, Clerk, Base44 auth, etc.), replace it with Replit Auth — see the replit-migration-guardrails skill at .local/secondary_skills/replit-migration-guardrails/SKILL.md. Skip if the app has no login flow. (App uses Django's built-in auth — no external auth provider to replace)
[x] 4. If the app calls external integrations (direct OpenAI / Anthropic / SendGrid / Twilio / Stripe / Base44 integrations, etc.), replace them with Replit integrations. Skip if none apply. (No external API integrations found)
[x] 5. Verify the project works end-to-end
[x] 6. REFONTE SYSTÈME: Suppression anciens rôles (Directeur Général, Adjoint, Censeur, Préfet) — conserve uniquement Directeur et Professeur
[x] 7. Espace Directeur: CRUD complet Élèves, Professeurs, Cours + consultation Notes
[x] 8. Espace Professeur: CRUD complet Notes (Ajouter, Modifier, Supprimer) par évaluation
[x] 9. Migration accounts.0004 pour suppression champ titre de Directeur
[x] 10. Mise à jour navigation sidebar directeur + templates (btn-xs, pages notes, cours, professeurs)
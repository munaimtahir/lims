# Non-Blocking Next Actions

1. **Pathologist permission:** Add pathologist demo user to Django Group "Pathologist" in `create_demo_users` so pathologist can verify results without using admin.

2. **Media permissions:** Ensure media directory is writable by container user (e.g., chown to appuser UID or set 775 with correct group) in Dockerfile or bootstrap script.

3. **Test catalog seeding:** Run `seed_test_catalog --clear` only when no orders exist, or run `catalog_ensure_minimum_parameters` after initial catalog load to add parameters to tests.

4. **Automated test:** Add pytest test for `filter_queryset_for_branches` with null branch to prevent regression.

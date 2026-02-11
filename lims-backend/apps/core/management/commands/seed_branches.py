from django.core.management.base import BaseCommand

from apps.core.models import Branch, BranchCapability, Tenant, get_default_tenant


class Command(BaseCommand):
    help = "Seed default branches for a tenant (HQ '00' plus sample branches)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--tenant",
            type=str,
            help="Tenant code to seed branches for (default: LAB).",
            default=None,
        )
        parser.add_argument(
            "--include-samples",
            action="store_true",
            help="Also create sample branches 01, 02, 03 in collect-only mode.",
        )

    def handle(self, *args, **options):
        tenant_code = options.get("tenant")
        include_samples = options.get("include_samples")

        tenant = (
            Tenant.objects.filter(code=tenant_code).first()
            if tenant_code
            else get_default_tenant()
        )

        if not tenant:
            self.stderr.write(self.style.ERROR("Tenant not found and could not be created."))
            return

        created = []
        hq, hq_created = Branch.objects.get_or_create(
            tenant=tenant,
            code="00",
            defaults={
                "name": "Head Office",
                "capability_mode": BranchCapability.HQ_PROCESSING,
                "is_hq": True,
                "is_active": True,
            },
        )
        if hq_created:
            created.append("00")

        if include_samples:
            samples = [
                ("01", "Branch 01"),
                ("02", "Branch 02"),
                ("03", "Branch 03"),
            ]
            for code, name in samples:
                _, c = Branch.objects.get_or_create(
                    tenant=tenant,
                    code=code,
                    defaults={
                        "name": name,
                        "capability_mode": BranchCapability.COLLECT_ONLY,
                        "is_active": True,
                    },
                )
                if c:
                    created.append(code)

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created branches for tenant {tenant.code}: {', '.join(created)}"
                )
            )
        else:
            self.stdout.write(self.style.WARNING("No new branches created (already exist)."))

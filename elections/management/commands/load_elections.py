import json
import os
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware, get_current_timezone

from elections.models.elections import Election
from elections.models.positions import Position
from elections.models.candidates import Candidate
from accounts.models import Department, User  # adjust if Department/User are elsewhere


class Command(BaseCommand):
    help = "Load elections, positions, and candidates from a JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            "json_file",
            type=str,
            help="Path to the JSON file containing elections data"
        )

    def handle(self, *args, **kwargs):
        json_file = kwargs["json_file"]

        if not os.path.exists(json_file):
            self.stderr.write(self.style.ERROR(f"File not found: {json_file}"))
            return

        with open(json_file, "r") as f:
            data = json.load(f)

        elections_data = data.get("elections", [])
        tz = get_current_timezone()

        for election_data in elections_data:
            # make datetime fields timezone-aware
            start_date = parse_datetime(election_data["start_date"])
            end_date = parse_datetime(election_data["end_date"])
            if start_date and not start_date.tzinfo:
                start_date = make_aware(start_date, tz)
            if end_date and not end_date.tzinfo:
                end_date = make_aware(end_date, tz)

            # ✅ Link school/department properly (expecting actual instances or null)
            school_instance = None
            if election_data.get("school"):
                school_instance = Department.objects.filter(name=election_data["school"]).first()

            department_instance = None
            if election_data.get("department"):
                department_instance = Department.objects.filter(name=election_data["department"]).first()

            election, created = Election.objects.get_or_create(
                title=election_data["title"],
                defaults={
                    "description": election_data.get("description", ""),
                    "start_date": start_date,
                    "end_date": end_date,
                    "school": school_instance,
                    "department": department_instance,
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created election: {election.title}"))
            else:
                self.stdout.write(self.style.WARNING(f"Election already exists: {election.title}"))

            # process positions
            for pos_data in election_data.get("positions", []):
                position_defaults = {
                    "description": pos_data.get("description", ""),
                    "eligible_levels": pos_data.get("eligible_levels", []),
                    "gender": pos_data.get("gender", "A"),  # default All
                }

                position, pos_created = Position.objects.get_or_create(
                    election=election,
                    title=pos_data["title"],
                    defaults=position_defaults
                )

                if pos_created:
                    self.stdout.write(self.style.SUCCESS(f"  Added position: {position.title}"))
                else:
                    for field, value in position_defaults.items():
                        setattr(position, field, value)
                    position.save()

                # ✅ handle ManyToMany eligible_departments by name
                dept_names = pos_data.get("eligible_departments", [])
                if dept_names:
                    depts = Department.objects.filter(name__in=dept_names)
                    position.eligible_departments.set(depts)

                # process candidates
                for cand_data in pos_data.get("candidates", []):
                    try:
                        student_obj = User.objects.get(index_number=cand_data["student"])
                    except User.DoesNotExist:
                        self.stderr.write(self.style.ERROR(
                            f"    ❌ User with index_number '{cand_data['student']}' not found"
                        ))
                        continue

                    candidate_defaults = {
                        "bio": cand_data.get("bio", ""),
                        "manifesto": cand_data.get("manifesto", ""),
                        "campaign_keywords": cand_data.get("campaign_keywords", []),
                        # 'image' removed for now
                    }

                    candidate, cand_created = Candidate.objects.get_or_create(
                        position=position,
                        student=student_obj,
                        defaults=candidate_defaults
                    )

                    if cand_created:
                        self.stdout.write(self.style.SUCCESS(f"    Added candidate: {student_obj.index_number}"))
                    else:
                        for field, value in candidate_defaults.items():
                            setattr(candidate, field, value)
                        candidate.save()
                        self.stdout.write(self.style.WARNING(f"    Updated candidate: {student_obj.index_number}"))

        self.stdout.write(self.style.SUCCESS("Elections data loaded successfully!"))

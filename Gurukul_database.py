"""
gurukul_assigner.py

Gurukul Admissions System - Student Assignment Logic
----------------------------------------------------
Assigns students to classes based on:
- Preferences (ranked)
- Eligibility rules (age, prerequisites, test score, fee, student type)
- Class capacities
- School-specific grouping

Uses a greedy priority-based approach:
1. Process per school
2. Consider only eligible preferences
3. Sort by preference rank (1 = highest), then submission date (earliest first)
4. Assign if capacity remains, otherwise waitlist/deny

Outputs:
- enrollments_new.csv
- applications_updated.csv
- Console summary of results

Usage:
    python gurukul_assigner.py
"""

import pandas as pd
from datetime import datetime


def has_prereq(completed_str, prereq_str):
    """Check if student has completed all required prerequisite classes."""
    if pd.isna(prereq_str) or prereq_str.strip() == '':
        return True
    completed = set(str(completed_str).split(',')) if pd.notna(completed_str) else set()
    required = set(str(prereq_str).split(','))
    return required.issubset(completed)


def is_eligible(student_row, class_row):
    """Check if a student meets all eligibility criteria for a class."""
    # Age checks
    if pd.notna(class_row['min_age']) and student_row['age'] < class_row['min_age']:
        return False, "Age below minimum"
    if pd.notna(class_row['max_age']) and student_row['age'] > class_row['max_age']:
        return False, "Age above maximum"

    # Fee requirement
    if class_row['fee_required'] and not student_row['fee_paid']:
        return False, "Fee not paid"

    # Test score
    if pd.notna(class_row['min_score']) and pd.notna(student_row['test_score']):
        if student_row['test_score'] < class_row['min_score']:
            return False, "Test score below minimum"

    # Prerequisites
    if not has_prereq(student_row['completed_courses'], class_row['prerequisites']):
        return False, "Missing prerequisite(s)"

    # Student type restrictions
    if pd.notna(class_row['student_type_restrictions']):
        allowed = set(class_row['student_type_restrictions'].split(','))
        if student_row['student_type'] not in allowed:
            return False, f"Type '{student_row['student_type']}' not allowed"

    return True, "Eligible"


def assign_students():
    # ────────────────────────────────────────────────
    # 1. Load data
    # ────────────────────────────────────────────────
    try:
        classes_df     = pd.read_csv('classes.csv')
        students_df    = pd.read_csv('students.csv')
        preferences_df = pd.read_csv('preferences.csv')
        applications_df = pd.read_csv('applications.csv')
    except FileNotFoundError as e:
        print(f"Error: Missing CSV file → {e}")
        return

    # Ensure dates are parsed
    preferences_df['submission_date'] = pd.to_datetime(preferences_df['submission_date'])

    # Merge preferences with student & class info
    merged = preferences_df.merge(students_df, on='student_id', how='left') \
                           .merge(classes_df, on='class_id', how='left') \
                           .merge(applications_df[['student_id', 'school_id']], on='student_id', how='left')

    # Remove rows with missing critical data
    merged = merged.dropna(subset=['student_id', 'class_id', 'school_id', 'rank'])

    # ────────────────────────────────────────────────
    # 2. Track results
    # ────────────────────────────────────────────────
    enrollments = []
    application_updates = []
    rejection_reasons = []

    # Working copy of capacities
    capacities = classes_df.set_index('class_id')['capacity'].to_dict()
    remaining_capacity = capacities.copy()

    # ────────────────────────────────────────────────
    # 3. Process each school separately
    # ────────────────────────────────────────────────
    for school_id in sorted(merged['school_id'].unique()):
        print(f"\nProcessing School {school_id} ...")

        school_data = merged[merged['school_id'] == school_id].copy()

        # Evaluate eligibility for every preference
        school_data[['eligible', 'reason']] = school_data.apply(
            lambda row: pd.Series(is_eligible(row, row)), axis=1
        )

        # Keep only eligible preferences
        eligible_prefs = school_data[school_data['eligible']].copy()

        if eligible_prefs.empty:
            print("  No eligible preferences found for this school.")
            continue

        # Sort: best preference first (rank 1), then earliest submission, then highest score
        eligible_prefs = eligible_prefs.sort_values(
            by=['rank', 'submission_date', 'test_score'],
            ascending=[True, True, False],
            na_position='last'
        )

        # Group by student to preserve preference order per student
        for student_id, group in eligible_prefs.groupby('student_id', sort=False):
            assigned = False
            for _, pref in group.iterrows():
                cid = pref['class_id']

                if remaining_capacity.get(cid, 0) > 0:
                    # Assign!
                    enrollments.append({
                        'enrollment_id': f"E{len(enrollments)+1001:04d}",
                        'student_id': student_id,
                        'class_id': cid,
                        'enrollment_date': datetime.now().strftime('%Y-%m-%d'),
                        'status': 'Enrolled'
                    })

                    remaining_capacity[cid] -= 1
                    assigned = True

                    application_updates.append({
                        'student_id': student_id,
                        'school_id': school_id,
                        'status': 'Approved',
                        'class_id': cid,          # optional: last assigned class
                        'assigned_date': datetime.now().strftime('%Y-%m-%d')
                    })
                    break

            if not assigned:
                # No spots in any preferred class
                top_choice = group.iloc[0]['class_id'] if not group.empty else None
                application_updates.append({
                    'student_id': student_id,
                    'school_id': school_id,
                    'status': 'Waitlist',     # or 'Denied' depending on policy
                    'class_id': top_choice,
                    'assigned_date': None
                })
                rejection_reasons.append({
                    'student_id': student_id,
                    'reason': 'No available capacity in preferred classes'
                })

    # ────────────────────────────────────────────────
    # 4. Save outputs
    # ────────────────────────────────────────────────
    if enrollments:
        pd.DataFrame(enrollments).to_csv('enrollments_new.csv', index=False)
        print(f"\nCreated {len(enrollments)} enrollments → enrollments_new.csv")

    # Update applications (simplified merge)
    if application_updates:
        updates_df = pd.DataFrame(application_updates)
        # In production: merge with original applications on student_id & school_id
        updates_df.to_csv('applications_updated.csv', index=False)
        print(f"Updated application statuses → applications_updated.csv")

    # Summary
    print("\nSummary:")
    print(f"Total assignments made: {len(enrollments)}")
    print("Remaining capacity per class:")
    for cid, rem in sorted(remaining_capacity.items()):
        original = capacities.get(cid, 0)
        filled = original - rem
        print(f"  Class {cid:3d}: {filled:2d}/{original:2d} filled ({rem} left)")

    if rejection_reasons:
        print(f"\n{len(rejection_reasons)} students waitlisted/denied")


if __name__ == "__main__":
    print("Gurukul Admissions Assignment")
    print("=============================")
    assign_students()
    print("\nDone.")
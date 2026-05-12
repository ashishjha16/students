from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import View

from student_management_app.forms import EditResultForm
from student_management_app.models import (Students, Subjects, StudentResult, SessionYearModel)


class EditResultViewClass(View):

    def get(self, request, *args, **kwargs):

        staff_id = request.user.id

        edit_result_form = EditResultForm(
            staff_id=staff_id
        )

        subjects = Subjects.objects.filter(
            staff_id=staff_id
        )

        session_years = SessionYearModel.object.all()

        return render(
            request,
            "staff_template/edit_student_result.html",
            {
                "form": edit_result_form,
                "subjects": subjects,
                "session_years": session_years
            }
        )

    def post(self, request, *args, **kwargs):

        form = EditResultForm(
            staff_id=request.user.id,
            data=request.POST
        )

        if form.is_valid():

            student_admin_id = form.cleaned_data['student_ids']
            assignment_marks = form.cleaned_data['assignment_marks']
            ct1_marks = form.cleaned_data['ct1_marks']
            ct2_marks = form.cleaned_data['ct2_marks']
            midsem_marks = form.cleaned_data['midsem_marks']
            endsem_marks = form.cleaned_data['endsem_marks']
            subject_id = form.cleaned_data['subject_id']

            student_obj = Students.objects.get(
                admin=student_admin_id
            )

            subject_obj = Subjects.objects.get(
                id=subject_id
            )

            # ✅ FIX: use filter().first() instead of get()
            result = StudentResult.objects.filter(
                subject_id=subject_obj,
                student_id=student_obj
            ).first()

            if result:
                # UPDATE
                result.assignment_marks = assignment_marks
                result.ct1_marks = ct1_marks
                result.ct2_marks = ct2_marks
                result.midsem_marks = midsem_marks
                result.endsem_marks = endsem_marks
                result.save()

                messages.success(
                    request,
                    "Successfully Updated Result"
                )

            else:
                # CREATE (important fix)
                StudentResult.objects.create(
                    student_id=student_obj,
                    subject_id=subject_obj,
                    assignment_marks=assignment_marks,
                    ct1_marks=ct1_marks,
                    ct2_marks=ct2_marks,
                    midsem_marks=midsem_marks,
                    endsem_marks=endsem_marks
                )

                messages.success(
                    request,
                    "Result Created Successfully"
                )

            return HttpResponseRedirect(
                reverse("edit_student_result")
            )

        else:

            messages.error(
                request,
                "Failed to Update Result"
            )

            form = EditResultForm(
                request.POST,
                staff_id=request.user.id
            )

            return render(
                request,
                "staff_template/edit_student_result.html",
                {"form": form}
            )
from django.http import HttpResponseRedirect
from django.shortcuts import render
import datetime
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from student_management_app.models import Notice
from student_management_app.models import Assignment

import json

from django.urls import reverse

from student_management_app.models import Subjects, Students, AttendanceReport, Attendance, CustomUser, FeedBackStudent, \
    LeaveReportStudent, SessionYearModel, Courses,StudentResult


def student_home(request, course=None):

    # =========================
    # GET STUDENT
    # =========================

    student_obj = Students.objects.get(
        admin=request.user.id
    )



    # =========================
    # ATTENDANCE COUNTS
    # =========================

    attendance_total = AttendanceReport.objects.filter(
        student_id=student_obj
    ).count()

    attendance_present = AttendanceReport.objects.filter(
        student_id=student_obj,
        status=True
    ).count()

    attendance_absent = AttendanceReport.objects.filter(
        student_id=student_obj,
        status=False
    ).count()



    # =========================
    # ATTENDANCE PERCENTAGE
    # =========================

    if attendance_total > 0:

        attendance_percentage = (
            attendance_present / attendance_total
        ) * 100

    else:

        attendance_percentage = 0



    # =========================
    # COURSE & SUBJECTS
    # =========================

    course = Courses.objects.get(
        id=student_obj.course_id.id
    )

    subjects = Subjects.objects.filter(
        course_id=course
    ).count()

    subjects_data = Subjects.objects.filter(
        course_id=course
    )



    # =========================
    # SESSION
    # =========================

    session_obj = SessionYearModel.object.get(
        id=student_obj.session_year_id.id
    )



    # =========================
    # SUBJECT-WISE ATTENDANCE
    # =========================

    subject_name = []

    data_present = []

    data_absent = []

    subject_data = Subjects.objects.filter(
        course_id=student_obj.course_id
    )

    for subject in subject_data:

        attendance = Attendance.objects.filter(
            subject_id=subject.id
        )

        attendance_present_count = AttendanceReport.objects.filter(
            attendance_id__in=attendance,
            status=True,
            student_id=student_obj.id
        ).count()

        attendance_absent_count = AttendanceReport.objects.filter(
            attendance_id__in=attendance,
            status=False,
            student_id=student_obj.id
        ).count()

        subject_name.append(
            subject.subject_name
        )

        data_present.append(
            attendance_present_count
        )

        data_absent.append(
            attendance_absent_count
        )



    # =========================
    # RENDER TEMPLATE
    # =========================

    return render(

        request,

        "student_template/student_home_template.html",

        {

            "total_attendance": attendance_total,

            "attendance_absent": attendance_absent,

            "attendance_present": attendance_present,

            "attendance_percentage": attendance_percentage,

            "subjects": subjects,

            "data_name": subject_name,

            "data1": data_present,

            "data2": data_absent

        }

    )

def student_view_attendance(request):
    student=Students.objects.get(admin=request.user.id)
    course=student.course_id
    subjects=Subjects.objects.filter(course_id=course)
    return render(request,"student_template/student_view_attendance.html",{"subjects":subjects})

def student_view_attendance_post(request):
    subject_id=request.POST.get("subject")
    start_date=request.POST.get("start_date")
    end_date=request.POST.get("end_date")

    start_data_parse=datetime.datetime.strptime(start_date,"%Y-%m-%d").date()
    end_data_parse=datetime.datetime.strptime(end_date,"%Y-%m-%d").date()
    subject_obj=Subjects.objects.get(id=subject_id)
    user_object=CustomUser.objects.get(id=request.user.id)
    stud_obj=Students.objects.get(admin=user_object)

    attendance=Attendance.objects.filter(attendance_date__range=(start_data_parse,end_data_parse),subject_id=subject_obj)
    attendance_reports=AttendanceReport.objects.filter(attendance_id__in=attendance,student_id=stud_obj)
    return render(request,"student_template/student_attendance_data.html",{"attendance_reports":attendance_reports})

def student_apply_leave(request):
    staff_obj = Students.objects.get(admin=request.user.id)
    leave_data=LeaveReportStudent.objects.filter(student_id=staff_obj)
    return render(request,"student_template/student_apply_leave.html",{"leave_data":leave_data})

def student_apply_leave_save(request):
    if request.method!="POST":
        return HttpResponseRedirect(reverse("student_apply_leave"))
    else:
        leave_date=request.POST.get("leave_date")
        leave_msg=request.POST.get("leave_msg")

        student_obj=Students.objects.get(admin=request.user.id)
        try:
            leave_report=LeaveReportStudent(student_id=student_obj,leave_date=leave_date,leave_message=leave_msg,leave_status=0)
            leave_report.save()
            messages.success(request, "Successfully Applied for Leave")
            return HttpResponseRedirect(reverse("student_apply_leave"))
        except:
            messages.error(request, "Failed To Apply for Leave")
            return HttpResponseRedirect(reverse("student_apply_leave"))


def student_feedback(request):
    staff_id=Students.objects.get(admin=request.user.id)
    feedback_data=FeedBackStudent.objects.filter(student_id=staff_id)
    return render(request,"student_template/student_feedback.html",{"feedback_data":feedback_data})

def student_feedback_save(request):
    if request.method!="POST":
        return HttpResponseRedirect(reverse("student_feedback"))
    else:
        feedback_msg=request.POST.get("feedback_msg")

        student_obj=Students.objects.get(admin=request.user.id)
        try:
            feedback=FeedBackStudent(student_id=student_obj,feedback=feedback_msg,feedback_reply="")
            feedback.save()
            messages.success(request, "Successfully Sent Feedback")
            return HttpResponseRedirect(reverse("student_feedback"))
        except:
            messages.error(request, "Failed To Send Feedback")
            return HttpResponseRedirect(reverse("student_feedback"))

def student_profile(request):
    user=CustomUser.objects.get(id=request.user.id)
    student=Students.objects.get(admin=user)
    return render(request,"student_template/student_profile.html",{"user":user,"student":student})

def student_profile_save(request):
    if request.method!="POST":
        return HttpResponseRedirect(reverse("student_profile"))
    else:
        first_name=request.POST.get("first_name")
        last_name=request.POST.get("last_name")
        password=request.POST.get("password")
        address=request.POST.get("address")
        try:
            customuser=CustomUser.objects.get(id=request.user.id)
            customuser.first_name=first_name
            customuser.last_name=last_name
            if password!=None and password!="":
                customuser.set_password(password)
            customuser.save()

            student=Students.objects.get(admin=customuser)
            student.address=address
            student.save()
            messages.success(request, "Successfully Updated Profile")
            return HttpResponseRedirect(reverse("student_profile"))
        except:
            messages.error(request, "Failed to Update Profile")
            return HttpResponseRedirect(reverse("student_profile"))

def student_view_result(request):
    student=Students.objects.get(admin=request.user.id)
    studentresult=StudentResult.objects.filter(student_id=student.id)
    return render(request,"student_template/student_result.html",{"studentresult":studentresult})

def student_attendance_calendar(request):

    return render(
        request,
        "student_template/student_attendance_calendar.html"
    )




@csrf_exempt
def get_student_attendance_by_date(request):

    selected_date = request.POST.get('attendance_date')

    student = Students.objects.get(admin=request.user.id)

    attendance_data = AttendanceReport.objects.filter(
        student_id=student,
        attendance_id__attendance_date=selected_date
    )

    list_data = []

    for attendance in attendance_data:

        data_small = {
            "subject": attendance.attendance_id.subject_id.subject_name,
            "status": "Present" if attendance.status else "Absent"
        }

        list_data.append(data_small)

    return JsonResponse(list_data, safe=False)
def student_attendance_calendar(request):

    student = Students.objects.get(admin=request.user.id)

    attendance = AttendanceReport.objects.filter(
        student_id=student
    )

    events = []

    for att in attendance:

        if att.status:

            color = "green"
            title = "Present"

        else:

            color = "red"
            title = "Absent"

        events.append({

            "title": title,

            "start":
            str(att.attendance_id.attendance_date),

            "color": color

        })

    return JsonResponse(events, safe=False)

def student_view_notice(request):

    notices = Notice.objects.all().order_by('-id')

    return render(
        request,
        "student_template/student_notice.html",
        {"notices": notices}
    )
def student_view_assignment(request):

    student = Students.objects.get(
        admin=request.user.id
    )

    assignments = Assignment.objects.filter(
        subject__course_id=student.course_id
    ).order_by('-id')

    return render(
        request,
        "student_template/student_assignment.html",
        {"assignments": assignments}
    )
def student_grade_card(request):

    student = Students.objects.get(admin=request.user.id)

    results = StudentResult.objects.filter(
        student_id=student
    ).select_related("subject_id")

    return render(
        request,
        "student_template/student_grade_card.html",
        {"results": results}
    )
from __future__ import division

from django.contrib.sessions import serializers
from django.http import HttpResponse
import json
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from student_management_app.models import Notice
from student_management_app.models import Assignment
import openpyxl

from student_management_app.models import Subjects, SessionYearModel, Students, Attendance, AttendanceReport, \
    LeaveReportStaff, Staffs, FeedBackStaffs, CustomUser, Courses, NotificationStaffs, StudentResult, OnlineClassRoom

def staff_home(request):
    #For Fetch All Student Under Staff
    subjects=Subjects.objects.filter(staff_id=request.user.id)
    course_id_list=[]
    for subject in subjects:
        course=Courses.objects.get(id=subject.course_id.id)
        course_id_list.append(course.id)

    final_course=[]
    #removing Duplicate Course ID
    for course_id in course_id_list:
        if course_id not in final_course:
            final_course.append(course_id)

    students_count=Students.objects.filter(course_id__in=final_course).count()

    #Fetch All Attendance Count
    attendance_count=Attendance.objects.filter(subject_id__in=subjects).count()

    #Fetch All Approve Leave
    staff=Staffs.objects.get(admin=request.user.id)
    leave_count=LeaveReportStaff.objects.filter(staff_id=staff.id,leave_status=1).count()
    subject_count=subjects.count()

    #Fetch Attendance Data by Subject
    subject_list=[]
    attendance_list=[]
    for subject in subjects:
        attendance_count1=Attendance.objects.filter(subject_id=subject.id).count()
        subject_list.append(subject.subject_name)
        attendance_list.append(attendance_count1)

    students_attendance=Students.objects.filter(course_id__in=final_course)
    student_list=[]
    student_list_attendance_present=[]
    student_list_attendance_absent=[]
    for student in students_attendance:
        attendance_present_count=AttendanceReport.objects.filter(status=True,student_id=student.id).count()
        attendance_absent_count=AttendanceReport.objects.filter(status=False,student_id=student.id).count()
        student_list.append(student.admin.username)
        student_list_attendance_present.append(attendance_present_count)
        student_list_attendance_absent.append(attendance_absent_count)

    return render(request,"staff_template/staff_home_template.html",{"students_count":students_count,"attendance_count":attendance_count,"leave_count":leave_count,"subject_count":subject_count,"subject_list":subject_list,"attendance_list":attendance_list,"student_list":student_list,"present_list":student_list_attendance_present,"absent_list":student_list_attendance_absent})


def staff_take_attendance(request):
    subjects=Subjects.objects.filter(staff_id=request.user.id)
    session_years=SessionYearModel.object.all()
    return render(request,"staff_template/staff_take_attendance.html",{"subjects":subjects,"session_years":session_years})

@csrf_exempt
def get_students(request, year=None):

    subject_id = request.POST.get("subject")
    session_year = request.POST.get("session_year")
    year = request.POST.get("year")
    division = request.POST.get("division")

    subject = Subjects.objects.get(id=subject_id)

    session_model = SessionYearModel.object.get(
        id=session_year
    )

    # =====================================
    # FILTER STUDENTS
    # =====================================

    students = Students.objects.filter(
        course_id=subject.course_id,
        session_year_id=session_model
    )

    # OPTIONAL FILTERS

    if year and year != "":
        students = students.filter(year=year)

    if division and division != "":
        students = students.filter(division=division)

    list_data = []

    for student in students:

        # =====================================
        # EXISTING RESULT
        # =====================================

        student_result = StudentResult.objects.filter(
            student_id=student,
            subject_id=subject
        ).first()

        # =====================================
        # DISPLAY FUNCTION
        # =====================================

        def display_marks(value):

            if value == -1:
                return "AB"

            elif value is None:
                return "NA"

            else:
                return value

        # =====================================
        # RESULT VALUES
        # =====================================

        if student_result:

            assignment_marks = display_marks(
                student_result.assignment_marks
            )

            ct1_marks = display_marks(
                student_result.ct1_marks
            )

            ct2_marks = display_marks(
                student_result.ct2_marks
            )

            midsem_marks = display_marks(
                student_result.midsem_marks
            )

            practical_marks = display_marks(
                student_result.practical_marks
            )

            endsem_marks = display_marks(
                student_result.endsem_marks
            )

        else:

            assignment_marks = ""
            ct1_marks = ""
            ct2_marks = ""
            midsem_marks = ""
            practical_marks = ""
            endsem_marks = ""

        # =====================================
        # FINAL DATA
        # =====================================

        data_small = {

            "id": student.admin.id,

            "roll_no": (
                student.roll_no
                if student.roll_no
                else ""
            ),

            "name":
                str(student.admin.first_name) +
                " " +
                str(student.admin.last_name),

            "assignment_marks": assignment_marks,

            "ct1_marks": ct1_marks,

            "ct2_marks": ct2_marks,

            "midsem_marks": midsem_marks,

            "practical_marks": practical_marks,

            "endsem_marks": endsem_marks

        }

        list_data.append(data_small)

    return JsonResponse(
        json.dumps(list_data),
        content_type="application/json",
        safe=False
    )

@csrf_exempt
def save_attendance_data(request):

    student_ids = request.POST.get("student_ids")

    subject_id = request.POST.get("subject_id")

    attendance_date = request.POST.get("attendance_date")

    session_year_id = request.POST.get("session_year_id")

    subject_model = Subjects.objects.get(id=subject_id)

    session_model = SessionYearModel.object.get(
        id=session_year_id
    )

    json_student = json.loads(student_ids)

    try:

        # =========================
        # CHECK DUPLICATE ATTENDANCE
        # =========================

        attendance_exists = Attendance.objects.filter(
            subject_id=subject_model,
            attendance_date=attendance_date,
            session_year_id=session_model
        ).exists()

        if attendance_exists:

            return HttpResponse("EXISTS")

        # =========================
        # SAVE ATTENDANCE
        # =========================

        attendance = Attendance(
            subject_id=subject_model,
            attendance_date=attendance_date,
            session_year_id=session_model
        )

        attendance.save()

        for stud in json_student:

            student = Students.objects.get(
                admin=stud['id']
            )

            attendance_report = AttendanceReport(
                student_id=student,
                attendance_id=attendance,
                status=stud['status']
            )

            attendance_report.save()

        return HttpResponse("OK")

    except Exception as e:

        print(e)

        return HttpResponse("ERR")

def staff_update_attendance(request):
    subjects=Subjects.objects.filter(staff_id=request.user.id)
    session_year_id=SessionYearModel.object.all()
    return render(request,"staff_template/staff_update_attendance.html",{"subjects":subjects,"session_year_id":session_year_id})

@csrf_exempt
def get_attendance_dates(request):

    subject = request.POST.get("subject")

    session_year_id = request.POST.get("session_year_id")

    year = request.POST.get("year")

    division = request.POST.get("division")

    subject_obj = Subjects.objects.get(id=subject)

    session_year_obj = SessionYearModel.object.get(
        id=session_year_id
    )

    attendance = Attendance.objects.filter(

        subject_id=subject_obj,

        session_year_id=session_year_obj,

        attendancereport__student_id__year=year,

        attendancereport__student_id__division=division

    ).distinct()

    attendance_obj = []

    for attendance_single in attendance:

        data = {

            "id": attendance_single.id,

            "attendance_date":
            str(attendance_single.attendance_date),

            "session_year_id":
            attendance_single.session_year_id.id

        }

        attendance_obj.append(data)

    return JsonResponse(
        json.dumps(attendance_obj),
        safe=False
    )

@csrf_exempt
def get_attendance_student(request):

    attendance_date = request.POST.get(
        "attendance_date"
    )

    attendance = Attendance.objects.get(
        id=attendance_date
    )

    attendance_data = AttendanceReport.objects.filter(
        attendance_id=attendance
    )

    list_data = []

    for student in attendance_data:

        data_small = {

            "id": student.student_id.admin.id,

            "roll_no": str(student.student_id.roll_no),

            "name":
            str(student.student_id.admin.first_name)
            + " " +
            str(student.student_id.admin.last_name),

            "status": student.status

        }

        list_data.append(data_small)

    return JsonResponse(
        json.dumps(list_data),
        content_type="application/json",
        safe=False
    )

@csrf_exempt
def save_updateattendance_data(request):
    student_ids=request.POST.get("student_ids")
    attendance_date=request.POST.get("attendance_date")
    attendance=Attendance.objects.get(id=attendance_date)

    json_sstudent=json.loads(student_ids)


    try:
        for stud in json_sstudent:
             student=Students.objects.get(admin=stud['id'])
             attendance_report=AttendanceReport.objects.get(student_id=student,attendance_id=attendance)
             attendance_report.status=stud['status']
             attendance_report.save()
        return HttpResponse("OK")
    except:
        return HttpResponse("ERR")

def staff_apply_leave(request):
    staff_obj = Staffs.objects.get(admin=request.user.id)
    leave_data=LeaveReportStaff.objects.filter(staff_id=staff_obj)
    return render(request,"staff_template/staff_apply_leave.html",{"leave_data":leave_data})

def staff_apply_leave_save(request):
    if request.method!="POST":
        return HttpResponseRedirect(reverse("staff_apply_leave"))
    else:
        leave_date=request.POST.get("leave_date")
        leave_msg=request.POST.get("leave_msg")

        staff_obj=Staffs.objects.get(admin=request.user.id)
        try:
            leave_report=LeaveReportStaff(staff_id=staff_obj,leave_date=leave_date,leave_message=leave_msg,leave_status=0)
            leave_report.save()
            messages.success(request, "Successfully Applied for Leave")
            return HttpResponseRedirect(reverse("staff_apply_leave"))
        except:
            messages.error(request, "Failed To Apply for Leave")
            return HttpResponseRedirect(reverse("staff_apply_leave"))

def staff_feedback(request):
    staff_id=Staffs.objects.get(admin=request.user.id)
    feedback_data=FeedBackStaffs.objects.filter(staff_id=staff_id)
    return render(request,"staff_template/staff_feedback.html",{"feedback_data":feedback_data})

def staff_feedback_save(request):
    if request.method!="POST":
        return HttpResponseRedirect(reverse("staff_feedback_save"))
    else:
        feedback_msg=request.POST.get("feedback_msg")

        staff_obj=Staffs.objects.get(admin=request.user.id)
        try:
            feedback=FeedBackStaffs(staff_id=staff_obj,feedback=feedback_msg,feedback_reply="")
            feedback.save()
            messages.success(request, "Successfully Sent Feedback")
            return HttpResponseRedirect(reverse("staff_feedback"))
        except:
            messages.error(request, "Failed To Send Feedback")
            return HttpResponseRedirect(reverse("staff_feedback"))

def staff_profile(request):
    user=CustomUser.objects.get(id=request.user.id)
    staff=Staffs.objects.get(admin=user)
    return render(request,"staff_template/staff_profile.html",{"user":user,"staff":staff})

def staff_profile_save(request):
    if request.method!="POST":
        return HttpResponseRedirect(reverse("staff_profile"))
    else:
        first_name=request.POST.get("first_name")
        last_name=request.POST.get("last_name")
        address=request.POST.get("address")
        password=request.POST.get("password")
        try:
            customuser=CustomUser.objects.get(id=request.user.id)
            customuser.first_name=first_name
            customuser.last_name=last_name
            if password!=None and password!="":
                customuser.set_password(password)
            customuser.save()

            staff=Staffs.objects.get(admin=customuser.id)
            staff.address=address
            staff.save()
            messages.success(request, "Successfully Updated Profile")
            return HttpResponseRedirect(reverse("staff_profile"))
        except:
            messages.error(request, "Failed to Update Profile")
            return HttpResponseRedirect(reverse("staff_profile"))
def staff_add_result(request):
    subjects=Subjects.objects.filter(staff_id=request.user.id)
    session_years=SessionYearModel.object.all()
    return render(request,"staff_template/staff_add_result.html",{"subjects":subjects,"session_years":session_years})

def edit_student_result(request):

    subjects = Subjects.objects.filter(
        staff_id=request.user.id
    )

    session_years = SessionYearModel.object.all()

    return render(
        request,
        "staff_template/edit_student_result.html",
        {
            "subjects": subjects,
            "session_years": session_years
        }
    )

def save_edit_result(request):

    if request.method != "POST":
        return HttpResponseRedirect(
            reverse("edit_student_result")
        )

    try:

        # =========================
        # GET FORM DATA
        # =========================

        student_ids = request.POST.getlist(
            "student_ids"
        )

        subject_id = request.POST.get(
            "subject"
        )

        assignment_marks = request.POST.getlist(
            "assignment_marks"
        )

        ct1_marks = request.POST.getlist(
            "ct1_marks"
        )

        ct2_marks = request.POST.getlist(
            "ct2_marks"
        )

        midsem_marks = request.POST.getlist(
            "midsem_marks"
        )

        practical_marks = request.POST.getlist(
            "practical_marks"
        )

        endsem_marks = request.POST.getlist(
            "endsem_marks"
        )

        # =========================
        # SUBJECT OBJECT
        # =========================

        subject_obj = Subjects.objects.get(
            id=subject_id
        )

        # =========================
        # CLEAN FUNCTION
        # =========================

        def clean_marks(value):

            if value is None:
                return None

            value = value.strip().upper()

            if value == "":
                return None

            elif value == "AB":
                return -1

            elif value == "NA":
                return None

            else:
                return float(value)

        # =========================
        # LOOP THROUGH STUDENTS
        # =========================

        for i in range(len(student_ids)):

            student_obj = Students.objects.get(
                admin=student_ids[i]
            )

            result, created = StudentResult.objects.get_or_create(

                student_id=student_obj,
                subject_id=subject_obj

            )

            result.assignment_marks = clean_marks(
                assignment_marks[i]
            )

            result.ct1_marks = clean_marks(
                ct1_marks[i]
            )

            result.ct2_marks = clean_marks(
                ct2_marks[i]
            )

            result.midsem_marks = clean_marks(
                midsem_marks[i]
            )

            result.practical_marks = clean_marks(
                practical_marks[i]
            )

            result.endsem_marks = clean_marks(
                endsem_marks[i]
            )

            result.save()

        messages.success(
            request,
            "Results Updated Successfully"
        )

    except Exception as e:

        print("ERROR :", e)

        messages.error(
            request,
            "Failed To Update Result"
        )

    return HttpResponseRedirect(
        reverse("edit_student_result")
    )

def save_student_result(request):

    if request.method != "POST":
        return HttpResponseRedirect(
            reverse("staff_add_result")
        )

    try:

        # =========================
        # GET DATA FROM FORM
        # =========================

        student_ids = request.POST.getlist(
            "student_ids"
        )

        assignment_marks = request.POST.getlist(
            "assignment_marks"
        )

        ct1_marks = request.POST.getlist(
            "ct1_marks"
        )

        ct2_marks = request.POST.getlist(
            "ct2_marks"
        )

        midsem_marks = request.POST.getlist(
            "midsem_marks"
        )

        practical_marks = request.POST.getlist(
            "practical_marks"
        )

        endsem_marks = request.POST.getlist(
            "endsem_marks"
        )

        subject_id = request.POST.get(
            "subject"
        )

        subject_obj = Subjects.objects.get(
            id=subject_id
        )



        # =========================
        # CLEAN FUNCTION
        # =========================

        def clean(value):

            if value is None:
                return None

            value = value.strip().upper()

            if value == "":
                return None

            if value == "AB":
                return -1

            if value == "NA":
                return None

            return float(value)



        # =========================
        # LOOP ALL STUDENTS
        # =========================

        for i in range(len(student_ids)):

            student_obj = Students.objects.get(
                admin=student_ids[i]
            )

            result, created = StudentResult.objects.get_or_create(

                student_id=student_obj,

                subject_id=subject_obj

            )

            result.assignment_marks = clean(
                assignment_marks[i]
            )

            result.ct1_marks = clean(
                ct1_marks[i]
            )

            result.ct2_marks = clean(
                ct2_marks[i]
            )

            result.midsem_marks = clean(
                midsem_marks[i]
            )

            result.practical_marks = clean(
                practical_marks[i]
            )

            result.endsem_marks = clean(
                endsem_marks[i]
            )

            result.save()



        messages.success(
            request,
            "Result Saved Successfully"
        )

        return HttpResponseRedirect(
            reverse("staff_add_result")
        )



    except Exception as e:

        print("ERROR :", e)

        messages.error(
            request,
            "Failed To Save Result"
        )

        return HttpResponseRedirect(
            reverse("staff_add_result")
        )
@csrf_exempt
def fetch_result_student(request):

    subject_id = request.POST.get('subject_id')

    student_id = request.POST.get('student_id')

    student_obj = Students.objects.get(admin=student_id)

    result = StudentResult.objects.filter(
        student_id=student_obj.id,
        subject_id=subject_id
    ).exists()

    if result:

        result = StudentResult.objects.get(
            student_id=student_obj.id,
            subject_id=subject_id
        )

        result_data = {
            "assignment_marks": result.assignment_marks,
            "ct1_marks": result.ct1_marks,
            "ct2_marks": result.ct2_marks,
            "midsem_marks": result.midsem_marks,
            "endsem_marks": result.endsem_marks
        }

        return HttpResponse(json.dumps(result_data))

    else:
        return HttpResponse("False")

def staff_add_notice(request):

    return render(request,
                  "staff_template/add_notice.html")


def staff_add_notice_save(request):

    if request.method != "POST":
        return HttpResponseRedirect(
            reverse("staff_add_notice")
        )

    title = request.POST.get("title")
    message = request.POST.get("message")
    notice_file = request.FILES.get("notice_file")

    try:

        notice = Notice(
            title=title,
            message=message,
            file=notice_file
        )

        notice.save()

        messages.success(request,
                         "Notice Uploaded Successfully")

        return HttpResponseRedirect(
            reverse("staff_add_notice")
        )

    except:

        messages.error(request,
                       "Failed To Upload Notice")

        return HttpResponseRedirect(
            reverse("staff_add_notice")
        )
def staff_add_assignment(request):

    subjects = Subjects.objects.filter(
        staff_id=request.user.id
    )

    return render(
        request,
        "staff_template/add_assignment.html",
        {"subjects": subjects}
    )



def staff_add_assignment_save(request):

    if request.method != "POST":

        return HttpResponseRedirect(
            reverse("staff_add_assignment")
        )

    subject_id = request.POST.get("subject")

    title = request.POST.get("title")

    description = request.POST.get("description")

    assignment_file = request.FILES.get(
        "assignment_file"
    )

    try:

        subject = Subjects.objects.get(
            id=subject_id
        )

        assignment = Assignment(

            subject=subject,

            title=title,

            description=description,

            assignment_file=assignment_file

        )

        assignment.save()

        messages.success(
            request,
            "Assignment Uploaded Successfully"
        )

        return HttpResponseRedirect(
            reverse("staff_add_assignment")
        )

    except:

        messages.error(
            request,
            "Failed To Upload Assignment"
        )

        return HttpResponseRedirect(
            reverse("staff_add_assignment")
        )

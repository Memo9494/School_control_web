
from django.shortcuts import render, redirect


# Create your views here.
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from classes.models import Course, Attendance, Participation, CustomUser
from django.core.mail import EmailMessage
from django.views.decorators import gzip
from django.http import StreamingHttpResponse
from django.shortcuts import render
import cv2
import os
import face_recognition
import time
from django.contrib.admin.views.decorators import staff_member_required

import numpy as np
import threading
from ultralytics import YOLO
from pydantic import BaseModel
from collections import defaultdict
today = time.strftime("%Y-%m-%d")
alumni_asist_cont = 0

class HomeView(ListView):
    model = Course
    template_name = 'home.html'
    context_object_name = 'course_obj'
    

class CourseDetailView(DetailView):
    model = Course
    template_name = 'course_detail.html'
    context_object_name = 'course_obj'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['alumni_obj'] = CustomUser.objects.filter(courses=self.object, is_staff=False)
        context['attendance_obj'] = Attendance.objects.filter(course=self.object)
        context['participation_obj'] = Participation.objects.filter(course=self.object)
        context['teacher_obj'] = CustomUser.objects.filter(courses=self.object, is_staff=True)
        context['user_obj'] = self.request.user
        context['pk'] = self.object.id
        return context
    
#create a new view that redirects to the course detail view
def take_attendance(request, pk):
    return redirect('course_detail', pk=pk)

    


@staff_member_required
@gzip.gzip_page
def video_feed(request, pk):
    try:
        cam = VideoCamera(pk)
        return StreamingHttpResponse(gen(cam), content_type="multipart/x-mixed-replace;boundary=frame")
    except:
        pass
    return render(request, 'videostream.html', {'pk': pk})

def face_recog(frame, data_encodings, attendance_flag, alumni_list, track_id=None):
    data_face_locations = face_recognition.face_locations(frame) # Obtiene las coordenadas del rostro en la imagen
    if data_face_locations != []:                                # Si se detecta un rostro
        flag = True
        data_face_encodings = face_recognition.face_encodings(frame, data_face_locations) # Obtiene los encodings de los rostros del frame
        for face_encoding in data_face_encodings:
            matches = face_recognition.compare_faces(data_encodings, face_encoding) # resultados de la comparacion de rostros
            if True in matches:
                index = matches.index(True)
                if attendance_flag == False:
                    alumni_asist_cont[index] += 1
                    if track_id:
                        alumni_list[index]["track_id"] = track_id
                        
                else:
                    if alumni_list[index]["attendance"] == 0:
                        alumni_list[index]["delay"] = 1
                        alumni_list[index]["attendance"] = 1
                        
                    alumni_list[index]["participations"] += 1
                    print("[PROCESO] Participacion registrada")
                    name = alumni_list[index]["name"]
                    print("[PROCESO] ", name)
            else:
                name = "Desconocido"
    else:
        print("[PROCESO] Rostros no detectados]")
        flag = False
    return flag

class VideoCamera(object):


    def __init__(self, pk):
        
        self.start_time_class = round(time.time(),2)  # tiempo de incio de programa
        self.end_time_class = 25.0
        self.time_lim_attendance = 10.0
        self.attendance_taken = False
        self.fps = 0
        self.frame_count = 0
        self.start_time_fps = self.start_time_class
        self.f_circulo_names = []
        #get all students in the course
        self.cap = cv2.VideoCapture(0)
        
        id = pk
        self.course = Course.objects.get(id=id)
        print(self.course)
        print("[PROCESO] Iniciando programa")

        
        students =  CustomUser.objects.filter(courses=self.course)
        print(students)
        self.data_encodings = []
        self.alumni_list = {}
        self.num_alumni = 0
        self.terminado = False
        self.frame_count = 0
        self.fps_count = 0
        
        
        for student in students:
            
            matricula = student.username
            
            enc = student.face_encoding
            
            encoding = [float(x) for x in enc.split(",")]

            self.data_encodings.append(encoding)

            self.alumni_list[self.num_alumni] = {"name":matricula, "attendance": False, "delay":False, "participations":0} # Dicicionario por alumno -> Nombre:[asistencia, conteo]
            self.num_alumni += 1

        print(self.course)
        
        self.alumni_asist_cont = np.zeros(self.num_alumni, dtype=int)
        alumni_asist_cont = self.alumni_asist_cont


        self.model = YOLO('yolov8_models/yolov8n-pose.pt') # usar modelo de pose
        self.get_keypoint = GetKeypoint()
        self.stages = [None]*self.num_alumni
        print("[PROCESO] Modelo cargado")
        print('[PROCESO] Cargando camara...')
        
        print('[PROCESO] Camara conectada')



        (self.grabbed,self.frame) = self.cap.read()
        threading.Thread(target=self.update,args=()).start()
    def __del__(self):
        self.cap.release()
    
    def get_frame(self):

        frame = self.frame # Frame leido por la camara
        actual_time = round(time.time(),2) - self.start_time_class
        actual_time = round(actual_time,2)

        
        elapsed_time = time.time() - self.start_time_fps
        self.frame_count += 1 # Contador de frames por segundo (FPS)
        self.fps_count += 1 # Contador de frames por segundo (FPS)
        if actual_time > self.end_time_class:
            self.terminado = True
            print("[PROCESO] Tiempo de clase terminado")
        if self.terminado == True:
                attendancei = self.alumni_list[i]["attendance"]
                participationsi = self.alumni_list[i]["participations"]
                namei = self.alumni_list[i]["name"]
                Attendance.objects.create(course=self.course, user=CustomUser.objects.get(username=namei), is_attended =attendancei, date=today)
                Participation.objects.create(course=self.course, user=CustomUser.objects.get(username=namei), amount=participationsi, date = today) 
                #close the program
                self.cap.release()
                cv2.destroyAllWindows()
                print("[PROCESO] Programa terminado")
        

        results = self.model.track(frame, persist=True) 
        if (results[0] != []) and (results[0].boxes.id != None):
            track_ids = results[0].boxes.id.cpu().tolist()
            keypoints = results[0].keypoints.xy.cpu().numpy()
            for track_id, kpts in zip(track_ids, keypoints):
                # Nose coordinates
                n_x, n_y = kpts[self.get_keypoint.NOSE]
                # Ears coordinates
                rE_x, rE_y = kpts[self.get_keypoint.RIGHT_EAR]
                lE_x, lE_y = kpts[self.get_keypoint.LEFT_EAR]
                # Eyes coordinates
                rEy_x, rEy_y = kpts[self.get_keypoint.RIGHT_EYE]
                # Face distances
                ears_dist = lE_x - rE_x
                noseye_dist = n_y - rEy_y
                st_pt = (int(rE_x - (ears_dist*0.2)), int(n_y - ears_dist))
                st_pt_str = str(st_pt[0]) + "," + str(st_pt[1])
                ed_pt = (int(lE_x + (ears_dist*0.2)), int(n_y + (noseye_dist * 4)))
                ed_pt_str = str(ed_pt[0]) + "," + str(ed_pt[1])
                # cv2.rectangle(frame, st_pt, ed_pt, (0, 255, 0), 2)
                face_frame = frame[st_pt[1]:ed_pt[1], st_pt[0]:ed_pt[0]]
                face_frame = np.ascontiguousarray(face_frame)
                
                if actual_time < self.time_lim_attendance:
                    if self.frame_count % 12 == 0:
                        face_recog(face_frame, self.data_encodings, self.attendance_taken, self.alumni_list,track_id)
                    for element, attributes in self.alumni_list.items():
                        track_id_ = attributes.get('track_id', None)  # Obtiene el valor de 'track_id' o None si no existe
                        if track_id == track_id_:
                            name = self.alumni_list[element]["name"]
                            break
                        else:
                            name = "Desconocido"
                    cv2.rectangle(frame, (int(rE_x - (ears_dist*0.2)), int(n_y + (noseye_dist * 4))-10), (int(lE_x + (ears_dist*0.2)), int(n_y + (noseye_dist * 4))), (0,255,0), cv2.FILLED)
                    cv2.putText(frame, name, (int(rE_x - (ears_dist*0.2))+3,  int(n_y + (noseye_dist * 4))-2), cv2.FONT_HERSHEY_DUPLEX, 0.4, (255,255,255), 1)
                else:
                    # Visualize the results on the frame
                    frame = results[0].plot(boxes=False)
                    # Wrists coordinates
                    rW_x, rW_y = kpts[self.get_keypoint.RIGHT_WRIST]
                    lW_x, lW_y = kpts[self.get_keypoint.LEFT_WRIST]
                    
                    # Participation Counter
                    if rW_y < rEy_y :
                        self.stages[int(track_id-1)] = 0
                    if rW_y > rEy_y and self.stages[int(track_id-1)] == 0:
                        self.stages[int(track_id-1)]= 1
                        print("[PROCESO] Participación detectada")
                        face_recog(face_frame, self.data_encodings, attendance_taken, self.alumni_list)
                        
            if (actual_time > self.time_lim_attendance) and (attendance_taken == False):
                attendance_taken = True
                print("[PROCESO] Tiempo de asistencia a tiempo terminado")
                indices = [i for i, valor in enumerate(alumni_asist_cont) if valor >= 10] # Verificar si aparece mas de 10 veces en ese tiempo
                for i in indices:
                    self.alumni_list[i]["attendance"] = 1
                print("[PROCESO] Asistencia tomada")
        
        # Conteo de frames por segundo (FPS)
        if elapsed_time > 1:
                fps = round(self.fps_count / elapsed_time)
                self.fps_count = 0
                start_time_fps = time.time()
        text = f"{fps} fps"

        print(self.alumni_list)
        _, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes()
    def update(self):
        
        while True:
            (self.grabbed,self.frame) = self.cap.read()
        
        
def gen(camera):
    while True:
        frame = camera.get_frame()
        yield(b'--frame\r\n'
              b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n') 


class GetKeypoint(BaseModel):
    NOSE:           int = 0
    LEFT_EYE:       int = 1
    RIGHT_EYE:      int = 2
    LEFT_EAR:       int = 3
    RIGHT_EAR:      int = 4
    LEFT_SHOULDER:  int = 5
    RIGHT_SHOULDER: int = 6
    LEFT_ELBOW:     int = 7
    RIGHT_ELBOW:    int = 8
    LEFT_WRIST:     int = 9
    RIGHT_WRIST:    int = 10
    LEFT_HIP:       int = 11
    RIGHT_HIP:      int = 12
    LEFT_KNEE:      int = 13
    RIGHT_KNEE:     int = 14
    LEFT_ANKLE:     int = 15
    RIGHT_ANKLE:    int = 16

def attendance_statistics(request):
    # Obtener datos para el informe
    attendance_data = Attendance.objects.all()
    participation_data = Participation.objects.all()
    attendance_per_course = np.zeros(len(Course.objects.all()), dtype=int)
    participation_per_course = np.zeros(len(Course.objects.all()), dtype=int)
    courses_names = []

    for i in range(len(Course.objects.all())):
        Course.objects.all()[i].attendance_set.all()
        courses_names.append(Course.objects.all()[i].name)
        for j in range(len(Course.objects.all()[i].attendance_set.all())):
            attendance_per_course[i] += Course.objects.all()[i].attendance_set.all()[j].is_attended
        for j in range(len(Course.objects.all()[i].participation_set.all())):
            if Course.objects.all()[i].participation_set.all()[j].amount != None:
                participation_per_course[i] += Course.objects.all()[i].participation_set.all()[j].amount


    print(attendance_per_course)
    print(participation_per_course)
    print(courses_names)

    # Pasar los datos al template
    context = {
        # 'attendance_data': attendance_data,
        # 'participation_data': participation_data,
        'attendance_per_course': attendance_per_course,
        'participation_per_course': participation_per_course,
        'courses_names': courses_names
    }

    # Renderizar el template
    return render(request, 'attendance_statistics.html', context)


                # attendancei = self.alumni_list[i]["attendance"]
                # participationsi = self.alumni_list[i]["participations"]
                # Attendance.objects.create(course=self.course, user=CustomUser.objects.get(username=namei), is_attended =attendancei, date=today)
                # Participation.objects.create(course=self.course, user=CustomUser.objects.get(username=namei), amount=participationsi, date = today) 
                # self.terminado = True
            
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
import re
from pymongo import MongoClient
import openai

# Configura tu clave de API de OpenAI
openai.api_key = ""

# Configura MongoDB
client = MongoClient("217269f7-b137-4169-9f02-c27fb294f418")
db = client["guia_app"]

class InicioScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        layout.add_widget(Button(text="Registrarse", on_release=self.ir_a_registro))
        layout.add_widget(Button(text="Entrar", on_release=self.ir_a_entrar))
        layout.add_widget(Button(text="Historial de Chats", on_release=self.ir_a_historial))
        self.add_widget(layout)

    def ir_a_registro(self, instance):
        self.manager.current = 'registro'

    def ir_a_entrar(self, instance):
        self.manager.current = 'entrar'

    def ir_a_historial(self, instance):
        self.manager.current = 'historial'

class RegistroScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        self.correo = TextInput(hint_text="Correo Institucional")
        self.usuario = TextInput(hint_text="Nombre de Usuario")
        self.contraseña = TextInput(hint_text="Contraseña", password=True)
        layout.add_widget(self.correo)
        layout.add_widget(self.usuario)
        layout.add_widget(self.contraseña)
        layout.add_widget(Button(text="Registrar", on_release=self.registrar))
        self.add_widget(layout)

    def registrar(self, instance):
        if not re.match(r"[^@]+@outlook\.com", self.correo.text):
            print("Correo inválido")
        else:
            usuario_existente = db.usuarios.find_one({"correo": self.correo.text})
            if usuario_existente:
                print("El usuario ya está registrado")
            else:
                db.usuarios.insert_one({
                    "correo": self.correo.text,
                    "usuario": self.usuario.text,
                    "contraseña": self.contraseña.text
                })
                print("Registrado correctamente")
                self.manager.current = 'entrar'

class EntrarScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        self.identificador = TextInput(hint_text="Correo o Nombre de Usuario")
        self.contraseña = TextInput(hint_text="Contraseña", password=True)
        layout.add_widget(self.identificador)
        layout.add_widget(self.contraseña)
        layout.add_widget(Button(text="Entrar", on_release=self.entrar))
        self.add_widget(layout)

    def entrar(self, instance):
        usuario = db.usuarios.find_one({
            "$or": [{"correo": self.identificador.text}, {"usuario": self.identificador.text}],
            "contraseña": self.contraseña.text
        })
        if usuario:
            print("Inicio de sesión exitoso")
            self.manager.current = 'malla_curricular'
        else:
            print("Credenciales incorrectas")

class MallaCurricularScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        layout.add_widget(Label(text="Malla Curricular"))
        for materia in db.materias.find():
            layout.add_widget(Button(text=materia["nombre"], on_release=self.seleccionar_materia))
        layout.add_widget(Button(text="Salir", on_release=self.salir))
        self.add_widget(layout)

    def seleccionar_materia(self, instance):
        self.manager.current = 'temario'

    def salir(self, instance):
        self.manager.current = 'inicio'

class TemarioScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        layout.add_widget(Label(text="Temario"))
        # Aquí se deben listar los temas de la materia seleccionada
        layout.add_widget(Button(text="Generar Resumen", on_release=self.ir_a_resumen))
        layout.add_widget(Button(text="Generar Preguntas", on_release=self.ir_a_preguntas))
        layout.add_widget(Button(text="Salir", on_release=self.salir))
        self.add_widget(layout)

    def ir_a_resumen(self, instance):
        self.manager.current = 'generar_resumen'

    def ir_a_preguntas(self, instance):
        self.manager.current = 'generar_preguntas'

    def salir(self, instance):
        self.manager.current = 'malla_curricular'

class GenerarResumenScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        layout.add_widget(Label(text="Generar Resumen"))
        layout.add_widget(Button(text="Abrir Chatbot", on_release=self.ir_a_chatbot))
        self.add_widget(layout)

    def ir_a_chatbot(self, instance):
        self.manager.current = 'chatbot'

class GenerarPreguntasScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        layout.add_widget(Label(text="Generar Preguntas"))
        layout.add_widget(Button(text="Abrir Chatbot", on_release=self.ir_a_chatbot))
        self.add_widget(layout)

    def ir_a_chatbot(self, instance):
        self.manager.current = 'chatbot'

class ChatbotScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        self.entrada = TextInput(hint_text="Escribe tu pregunta aquí")
        layout.add_widget(self.entrada)
        layout.add_widget(Button(text="Enviar", on_release=self.enviar_pregunta))
        self.respuesta = Label(text="")
        layout.add_widget(self.respuesta)
        self.add_widget(layout)

    def enviar_pregunta(self, instance):
        pregunta = self.entrada.text
        respuesta = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": pregunta}]
        )
        self.respuesta.text = respuesta.choices[0].message['content']
        db.historial.insert_one({"pregunta": pregunta, "respuesta": self.respuesta.text})
        print("Pregunta enviada")

class HistorialScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        layout.add_widget(Label(text="Historial de Chats"))
        scroll = ScrollView()
        historial_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        historial_layout.bind(minimum_height=historial_layout.setter('height'))
        for chat in db.historial.find():
            historial_layout.add_widget(Label(text=f"Pregunta: {chat['pregunta']}\nRespuesta: {chat['respuesta']}"))
        scroll.add_widget(historial_layout)
        layout.add_widget(scroll)
        layout.add_widget(Button(text="Volver", on_release=self.volver))
        self.add_widget(layout)

    def volver(self, instance):
        self.manager.current = 'inicio'

class MiApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(InicioScreen(name='inicio'))
        sm.add_widget(RegistroScreen(name='registro'))
        sm.add_widget(EntrarScreen(name='entrar'))
        sm.add_widget(MallaCurricularScreen(name='malla_curricular'))
        sm.add_widget(TemarioScreen(name='temario'))
        sm.add_widget(GenerarResumenScreen(name='generar_resumen'))
        sm.add_widget(GenerarPreguntasScreen(name='generar_preguntas'))
        sm.add_widget(ChatbotScreen(name='chatbot'))
        sm.add_widget(HistorialScreen(name='historial'))
        return sm

if __name__ == '__main__':
    MiApp().run()

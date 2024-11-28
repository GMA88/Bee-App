from kivy.core.window import Window
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
import re
from pymongo import MongoClient
import openai

# Establece el tamaño de la ventana (ideal para aplicaciones móviles)
Window.size = (360, 640)  # 360x640 píxeles, tamaño común de pantalla de celular

# Configura tu clave de API de OpenAI
openai.api_key = ""  # Coloca tu clave aquí

# Configura MongoDB
client = MongoClient("mongodb://localhost:27017")  # Asegúrate de usar una URI válida
db = client["guia_app"]

# Crear un fondo con un color cian
class Background(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            # Dibuja un rectángulo de color para simular el fondo
            self.rect = Rectangle(size=self.size, pos=self.pos)
            self.color1 = Color(0, 1, 1, 1)  # Cian (inicio)
            self.rect.pos = self.pos
            self.rect.size = self.size

    def on_size(self, *args):
        self.rect.size = self.size
        self.rect.pos = self.pos

    def on_pos(self, *args):
        self.rect.pos = self.pos


# Pantalla de Historial de Chats
class HistorialScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=10, padding=[50, 150, 50, 50])  # Ajuste de padding
        layout.add_widget(Label(text="Historial de Chats"))
        
        # Aquí agregarías la lógica para mostrar el historial de chats desde la base de datos
        historial_chats = db.historial.find()  # Consulta los chats guardados en la base de datos
        for chat in historial_chats:
            layout.add_widget(Label(text=f"Chat: {chat.get('mensaje', 'Sin mensaje')}"))

        layout.add_widget(Button(text="Salir", size_hint=(None, None), size=(200, 50), on_release=self.salir))
        self.add_widget(layout)

    def salir(self, instance):
        self.manager.current = 'inicio'


# Pantalla de Inicio
class InicioScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Agrega el fondo cian
        self.add_widget(Background())

        # ScrollView para manejar desbordamiento
        scroll = ScrollView()

        # Layout principal
        layout = BoxLayout(orientation='vertical', spacing=20, padding=[20, 50, 20, 50], size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))  # Ajusta la altura según el contenido

        # Agrega botones al layout
        layout.add_widget(Button(text="Registrarse", size_hint=(1, None), height=50, on_release=self.ir_a_registro))
        layout.add_widget(Button(text="Entrar", size_hint=(1, None), height=50, on_release=self.ir_a_entrar))
        layout.add_widget(Button(text="Historial de Chats", size_hint=(1, None), height=50, on_release=self.ir_a_historial))

        # Añade el layout al ScrollView
        scroll.add_widget(layout)
        self.add_widget(scroll)

    def ir_a_registro(self, instance):
        self.manager.current = 'registro'

    def ir_a_entrar(self, instance):
        self.manager.current = 'entrar'

    def ir_a_historial(self, instance):
        self.manager.current = 'historial'


# Pantalla de Registro
class RegistroScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=10, padding=[50, 150, 50, 50])  # Ajuste de padding
        self.correo = TextInput(hint_text="Correo Institucional", size_hint=(None, None), size=(250, 40))
        self.usuario = TextInput(hint_text="Nombre de Usuario", size_hint=(None, None), size=(250, 40))
        self.contraseña = TextInput(hint_text="Contraseña", password=True, size_hint=(None, None), size=(250, 40))
        
        # Espaciado entre campos
        layout.add_widget(self.correo)
        layout.add_widget(self.usuario)
        layout.add_widget(self.contraseña)
        layout.add_widget(Button(text="Registrar", size_hint=(None, None), size=(200, 50), on_release=self.registrar))
        self.add_widget(layout)

    def registrar(self, instance):
        if not re.match(r"[^@]+@ugto\.mx", self.correo.text):  # Cambiamos la validación de correo
            print("Correo inválido. Debe ser un correo institucional de UGTO.")
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

# Pantalla de Entrar
class EntrarScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=10, padding=[50, 150, 50, 50])  # Ajuste de padding
        self.identificador = TextInput(hint_text="Correo o Nombre de Usuario", size_hint=(None, None), size=(250, 40))
        self.contraseña = TextInput(hint_text="Contraseña", password=True, size_hint=(None, None), size=(250, 40))
        
        layout.add_widget(self.identificador)
        layout.add_widget(self.contraseña)
        layout.add_widget(Button(text="Entrar", size_hint=(None, None), size=(200, 50), on_release=self.entrar))
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

# Pantalla de Malla Curricular
class MallaCurricularScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=10, padding=[50, 150, 50, 50])  # Ajuste de padding
        layout.add_widget(Label(text="Malla Curricular"))

        scroll = ScrollView()
        materias_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        materias_layout.bind(minimum_height=materias_layout.setter('height'))

        materias = list(db.materias.find())  # Convertimos el cursor a una lista
        if len(materias) == 0:  # Verificamos si no hay materias
            materias_layout.add_widget(Label(text="No hay materias disponibles"))
        else:
            for materia in materias:
                materias_layout.add_widget(
                    Button(text=materia["nombre"], size_hint=(None, None), size=(200, 50), on_release=self.seleccionar_materia)
                )
        
        scroll.add_widget(materias_layout)
        layout.add_widget(scroll)
        layout.add_widget(Button(text="Salir", size_hint=(None, None), size=(200, 50), on_release=self.salir))
        self.add_widget(layout)

    def seleccionar_materia(self, instance):
        print(f"Materia seleccionada: {instance.text}")
        self.manager.current = 'temario'

    def salir(self, instance):
        self.manager.current = 'inicio'

# Pantalla de Temario
class TemarioScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=10, padding=[50, 150, 50, 50])  # Ajuste de padding
        layout.add_widget(Label(text="Temario"))
        layout.add_widget(Button(text="Generar Resumen", size_hint=(None, None), size=(200, 50), on_release=self.ir_a_resumen))
        layout.add_widget(Button(text="Generar Preguntas", size_hint=(None, None), size=(200, 50), on_release=self.ir_a_preguntas))
        layout.add_widget(Button(text="Salir", size_hint=(None, None), size=(200, 50), on_release=self.salir))
        self.add_widget(layout)

    def ir_a_resumen(self, instance):
        self.manager.current = 'generar_resumen'

    def ir_a_preguntas(self, instance):
        self.manager.current = 'generar_preguntas'

    def salir(self, instance):
        self.manager.current = 'inicio'


# Pantalla de Generar Resumen
class GenerarResumenScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=10, padding=[50, 150, 50, 50])  # Ajuste de padding
        layout.add_widget(Label(text="Generar Resumen"))
        layout.add_widget(Button(text="Generar", size_hint=(None, None), size=(200, 50), on_release=self.generar_resumen))
        layout.add_widget(Button(text="Salir", size_hint=(None, None), size=(200, 50), on_release=self.salir))
        self.add_widget(layout)

    def generar_resumen(self, instance):
        # Lógica para generar el resumen
        print("Generando resumen...")

    def salir(self, instance):
        self.manager.current = 'inicio'


# Pantalla de Generar Preguntas
class GenerarPreguntasScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=10, padding=[50, 150, 50, 50])  # Ajuste de padding
        layout.add_widget(Label(text="Generar Preguntas"))
        layout.add_widget(Button(text="Generar", size_hint=(None, None), size=(200, 50), on_release=self.generar_preguntas))
        layout.add_widget(Button(text="Salir", size_hint=(None, None), size=(200, 50), on_release=self.salir))
        self.add_widget(layout)

    def generar_preguntas(self, instance):
        # Lógica para generar preguntas
        print("Generando preguntas...")

    def salir(self, instance):
        self.manager.current = 'inicio'


# Clase principal de la aplicación
class GuiaApp(App):
    def build(self):
        sm = ScreenManager()

        sm.add_widget(InicioScreen(name='inicio'))
        sm.add_widget(RegistroScreen(name='registro'))
        sm.add_widget(EntrarScreen(name='entrar'))
        sm.add_widget(MallaCurricularScreen(name='malla_curricular'))
        sm.add_widget(TemarioScreen(name='temario'))
        sm.add_widget(GenerarResumenScreen(name='generar_resumen'))
        sm.add_widget(GenerarPreguntasScreen(name='generar_preguntas'))
        sm.add_widget(HistorialScreen(name='historial'))  # Añadimos la pantalla de historial

        return sm


if __name__ == '__main__':
    GuiaApp().run()

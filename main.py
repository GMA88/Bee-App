import os
from pymongo import MongoClient
from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.core.window import Window
from dotenv import load_dotenv
import openai
from passlib.hash import pbkdf2_sha256  # Reemplazo de hashlib
import webbrowser
from fpdf import FPDF  # Librería para generar PDFs

# Cargar variables de entorno
load_dotenv()

# Conexión segura a MongoDB Atlas
client = MongoClient(os.getenv("MONGO_URI"))
db = client["guia_app"]

# Configura la clave de API de OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Función para hashear contraseñas
def hash_password(password):
    return pbkdf2_sha256.hash(password)

# Verificar contraseña, con manejo mejorado de errores
def verify_password(password, hashed):
    try:
        if pbkdf2_sha256.verify(password, hashed):
            return True
    except ValueError:
        print("El formato del hash no es válido. Probablemente la contraseña no está hasheada.")
    except Exception as e:
        print(f"Error al verificar la contraseña: {e}")
    return False

# Función para registrar un usuario
def register_user(email, username, password):
    if not email.endswith('@ugto.mx'):
        return "Debe usar un correo institucional que termine en @ugto.mx"
    if db.usuarios.find_one({"correo": email}):
        return "El correo ya está registrado"
    
    try:
        db.usuarios.insert_one({
            "correo": email,
            "usuario": username,
            "contraseña": hash_password(password)
        })
        return "Registro exitoso"
    except Exception as e:
        print(f"Error al registrar usuario: {e}")
        return "Hubo un problema al registrar. Intente nuevamente."

# Función para iniciar sesión
def login_user(email, password):
    try:
        user = db.usuarios.find_one({"correo": email})
        if user:
            print("Usuario encontrado en la base de datos.")
            hashed_password = user.get("contraseña")
            if verify_password(password, hashed_password):
                print("Contraseña verificada correctamente.")
                # Actualizar contraseña al nuevo formato si no estaba hasheada
                if not pbkdf2_sha256.identify(hashed_password):
                    print("Actualizando contraseña al nuevo formato.")
                    db.usuarios.update_one(
                        {"correo": email},
                        {"$set": {"contraseña": hash_password(password)}}
                    )
                return True
            else:
                print("La contraseña ingresada es incorrecta.")
        else:
            print("El usuario no existe en la base de datos.")
    except Exception as e:
        print(f"Error al iniciar sesión: {e}")
    return False

# Clase base para mostrar mensajes emergentes
class PopupMessage:
    @staticmethod
    def show_message(title, message):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Añadir un ScrollView para manejar mensajes largos
        scroll = ScrollView(size_hint=(1, 1))
        formatted_message = "\n".join(message.split(", "))  # Dividir los elementos en líneas separadas
        message_label = Label(text=formatted_message, size_hint_y=None, text_size=(400, None), valign='top', halign='left')
        message_label.bind(texture_size=message_label.setter('size'))
        scroll.add_widget(message_label)

        content.add_widget(scroll)

        close_button = Button(text="Cerrar", size_hint=(None, None), size=(200, 50))
        content.add_widget(close_button)

        popup = Popup(title=title, content=content, size_hint=(0.8, 0.8))
        close_button.bind(on_release=popup.dismiss)
        popup.open()

# Función para generar resumen usando la API de OpenAI
def generar_resumen(temas):
    try:
        prompt = f"Genera un resumen detallado para los siguientes temas, sin comentarios adicionales: {temas}"
        respuesta = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un asistente que genera resúmenes educativos."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        return respuesta["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Error al generar resumen: {e}")
        return "Error al generar el resumen. Inténtalo más tarde."

# Función para generar guía de estudio usando la API de OpenAI
def generar_guia(temas):
    try:
        prompt = f"Genera una guía de estudio con preguntas clave para los siguientes temas, sin comentarios adicionales: {temas}"
        respuesta = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un asistente que genera guías de estudio educativas."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        return respuesta["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Error al generar guía: {e}")
        return "Error al generar la guía de estudio. Inténtalo más tarde."

# Función para manejar preguntas o peticiones adicionales usando la API de OpenAI
def responder_pregunta(peticion):
    try:
        respuesta = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un asistente educativo capaz de responder preguntas y realizar tareas según lo solicitado."},
                {"role": "user", "content": peticion}
            ],
            max_tokens=500
        )
        return respuesta["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Error al responder la pregunta: {e}")
        return "Error al procesar tu petición. Inténtalo más tarde."
    
class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        self.layout.add_widget(Label(text="Correo Electrónico", size_hint_y=None, height=40))
        self.email_input = TextInput(size_hint_y=None, height=40, multiline=False)
        self.layout.add_widget(self.email_input)

        self.layout.add_widget(Label(text="Contraseña", size_hint_y=None, height=40))
        self.password_input = TextInput(password=True, size_hint_y=None, height=40, multiline=False)
        self.layout.add_widget(self.password_input)

        self.login_button = Button(text="Iniciar Sesión", size_hint_y=None, height=50)
        self.login_button.bind(on_release=self.iniciar_sesion)
        self.layout.add_widget(self.login_button)

        self.register_button = Button(text="Registrarse", size_hint_y=None, height=50)
        self.register_button.bind(on_release=self.ir_a_registro)
        self.layout.add_widget(self.register_button)

        self.add_widget(self.layout)

    def iniciar_sesion(self, instance):
        email = self.email_input.text.strip()
        password = self.password_input.text.strip()

        if login_user(email, password):
            self.manager.current = 'malla_curricular'
        else:
            PopupMessage.show_message("Error", "Correo o contraseña incorrectos")

    def ir_a_registro(self, instance):
        self.manager.current = 'register'

class RegisterScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        self.layout.add_widget(Label(text="Correo Electrónico Institucional", size_hint_y=None, height=40))
        self.email_input = TextInput(size_hint_y=None, height=40, multiline=False)
        self.layout.add_widget(self.email_input)

        self.layout.add_widget(Label(text="Nombre de Usuario", size_hint_y=None, height=40))
        self.username_input = TextInput(size_hint_y=None, height=40, multiline=False)
        self.layout.add_widget(self.username_input)

        self.layout.add_widget(Label(text="Contraseña", size_hint_y=None, height=40))
        self.password_input = TextInput(password=True, size_hint_y=None, height=40, multiline=False)
        self.layout.add_widget(self.password_input)

        self.register_button = Button(text="Registrarse", size_hint_y=None, height=50)
        self.register_button.bind(on_release=self.registrar_usuario)
        self.layout.add_widget(self.register_button)

        self.add_widget(self.layout)

    def registrar_usuario(self, instance):
        email = self.email_input.text.strip()
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()

        resultado = register_user(email, username, password)
        PopupMessage.show_message("Registro", resultado)
        if resultado == "Registro exitoso":
            self.manager.current = 'login'
            
class TemarioScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', spacing=20, padding=[20, 20, 20, 20])
        self.temas_checkbox = []
        self.add_widget(self.layout)

    def cargar_temas(self, materia):
        self.layout.clear_widgets()
        self.layout.add_widget(Label(text=f"Temario de {materia}", font_size='24sp', size_hint_y=None, height=50))

        scroll = ScrollView(size_hint=(1, 1))
        temas_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10, padding=[10, 10])
        temas_layout.bind(minimum_height=temas_layout.setter('height'))

        try:
            temas = db.materias.find_one({"nombre": materia})
            if temas and "temas" in temas:
                for tema in temas["temas"]:
                    tema_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
                    checkbox = CheckBox(size_hint=(None, None), size=(50, 50))
                    tema_label = Label(text=f"{tema.get('numero', '')}. {tema.get('titulo', 'Título desconocido')}")
                    tema_layout.add_widget(checkbox)
                    tema_layout.add_widget(tema_label)
                    self.temas_checkbox.append((checkbox, tema_label.text))
                    temas_layout.add_widget(tema_layout)
            else:
                temas_layout.add_widget(Label(text="No hay temas disponibles", size_hint=(1, None), height=40))
        except Exception as e:
            print(f"Error al cargar temas: {e}")
            temas_layout.add_widget(Label(text="Error al cargar temas", size_hint=(1, None), height=40))

        scroll.add_widget(temas_layout)
        self.layout.add_widget(scroll)

        # Añadir botones para generar resumen y guía de estudio
        botones_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=50)
        resumen_button = Button(text="Generar Resumen", size_hint=(None, None), size=(200, 50), on_release=self.generar_resumen)
        guia_button = Button(text="Generar Guía de Estudio", size_hint=(None, None), size=(200, 50), on_release=self.generar_guia)
        resumen_bot_button = Button(text="Enviar Resumen al Bot", size_hint=(None, None), size=(200, 50), on_release=self.enviar_resumen_al_bot)
        guia_bot_button = Button(text="Enviar Guía al Bot", size_hint=(None, None), size=(200, 50), on_release=self.enviar_guia_al_bot)
        telegram_button = Button(text="Probar Bot de Telegram", size_hint=(None, None), size=(200, 50), on_release=self.ir_a_telegram)
        botones_layout.add_widget(resumen_button)
        botones_layout.add_widget(guia_button)
        botones_layout.add_widget(resumen_bot_button)
        botones_layout.add_widget(guia_bot_button)
        botones_layout.add_widget(telegram_button)
        self.layout.add_widget(botones_layout)

    def generar_resumen(self, instance):
        seleccionados = [tema[1] for tema in self.temas_checkbox if tema[0].active]
        if not seleccionados:
            PopupMessage.show_message("Error", "Seleccione al menos un tema para generar el resumen.")
            return

        resumen = self.obtener_resumen_openai(seleccionados)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', size=16)
        pdf.cell(0, 10, txt="Resumen", ln=True, align='C')
        pdf.ln(10)  # Espaciado

        pdf.set_font("Arial", size=12)
        for tema in resumen.split('\n\n'):
            pdf.multi_cell(0, 10, txt=tema)
            pdf.ln(5)  # Espacio entre párrafos

        pdf.output("resumen.pdf")
        PopupMessage.show_message("Éxito", "Resumen generado y guardado como resumen.pdf.")

    def generar_guia(self, instance):
        seleccionados = [tema[1] for tema in self.temas_checkbox if tema[0].active]
        if not seleccionados:
            PopupMessage.show_message("Error", "Seleccione al menos un tema para generar la guía de estudio.")
            return

        guia = self.obtener_guia_openai(seleccionados)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', size=16)
        pdf.cell(0, 10, txt="Guía de Estudio", ln=True, align='C')
        pdf.ln(10)  # Espaciado

        pdf.set_font("Arial", size=12)
        for tema in guia.split('\n\n'):
            pdf.multi_cell(0, 10, txt=tema)
            pdf.ln(5)  # Espacio entre preguntas

        pdf.output("guia_estudio.pdf")
        PopupMessage.show_message("Éxito", "Guía de estudio generada y guardada como guia_estudio.pdf.")

    def enviar_resumen_al_bot(self, instance):
        seleccionados = [tema[1] for tema in self.temas_checkbox if tema[0].active]
        if not seleccionados:
            PopupMessage.show_message("Error", "Seleccione al menos un tema para enviar el resumen al bot.")
            return

        temas = ', '.join(seleccionados)
        webbrowser.open(f"https://t.me/beeDICIS_bot?start=resumen_{temas}")

    def enviar_guia_al_bot(self, instance):
        seleccionados = [tema[1] for tema in self.temas_checkbox if tema[0].active]
        if not seleccionados:
            PopupMessage.show_message("Error", "Seleccione al menos un tema para enviar la guía al bot.")
            return

        temas = ', '.join(seleccionados)
        webbrowser.open(f"https://t.me/beeDICIS_bot?start=guia_{temas}")

    def ir_a_telegram(self, instance):
        webbrowser.open("https://t.me/beeDICIS_bot")
        
    def obtener_resumen_openai(self, temas):
        try:
            prompt = f"Genera un resumen detallado para los siguientes temas, sin agregar comentarios al final: {', '.join(temas)}"
            respuesta = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un asistente que genera resúmenes educativos."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000
            )
            return respuesta["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"Error al generar resumen con OpenAI: {e}")
            return "Error al generar el resumen. Inténtelo de nuevo más tarde."

    def obtener_guia_openai(self, temas):
        try:
            prompt = f"Genera una guía de estudio con preguntas clave para los siguientes temas, sin agregar comentarios adicionales: {', '.join(temas)}"
            respuesta = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un asistente que genera guías de estudio educativas."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000
            )
            return respuesta["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"Error al generar guía con OpenAI: {e}")
            return "Error al generar la guía de estudio. Inténtelo de nuevo más tarde."

    def salir(self, instance):
        self.manager.current = 'malla_curricular'
        
class MallaCurricularScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=20, padding=[20, 20, 20, 20])
        layout.add_widget(Label(text="Malla Curricular", font_size='24sp', size_hint_y=None, height=50))

        scroll = ScrollView(size_hint=(1, None), size=(Window.width, Window.height * 0.8))
        materias_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10, padding=[10, 10])
        materias_layout.bind(minimum_height=materias_layout.setter('height'))

        try:
            semestres = db.materias.aggregate([
                {"$group": {"_id": "$semestre", "materias": {"$push": "$nombre"}}},
                {"$sort": {"_id": 1}}
            ])

            for semestre in semestres:
                semestre_id = semestre["_id"] if semestre["_id"] else "Sin nombre"
                materias_layout.add_widget(Label(text=str(semestre_id), font_size='20sp', size_hint_y=None, height=40))
                for materia in semestre["materias"]:
                    materia_nombre = materia if materia else "Materia desconocida"
                    materias_layout.add_widget(
                        Button(text=str(materia_nombre), size_hint_y=None, height=50, on_release=self.seleccionar_materia)
                    )

        except Exception as e:
            print(f"Error al cargar materias: {e}")
            materias_layout.add_widget(Label(text="Error al cargar materias", size_hint_y=None, height=40))

        scroll.add_widget(materias_layout)
        layout.add_widget(scroll)
        layout.add_widget(Button(text="Salir", size_hint=(None, None), size=(200, 50), on_release=self.salir))
        self.add_widget(layout)

    def seleccionar_materia(self, instance):
        print(f"Materia seleccionada: {instance.text}")
        self.manager.current = 'temario'
        self.manager.get_screen('temario').cargar_temas(instance.text)

    def salir(self, instance):
        self.manager.current = 'login'


class MainApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(RegisterScreen(name='register'))
        sm.add_widget(MallaCurricularScreen(name='malla_curricular'))
        sm.add_widget(TemarioScreen(name='temario'))
        return sm

if __name__ == '__main__':
    MainApp().run()

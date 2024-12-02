from kivy.core.window import Window  # Importar Window
from pymongo import MongoClient
from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
import openai
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import webbrowser

# Conexión a MongoDB Atlas
client = MongoClient("")  # Reemplaza con tu URI de conexión a MongoDB Atlas
db = client["guia_app"]

# Configura tu clave de API de OpenAI
openai.api_key = ""

class InicioScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=20, padding=[20, 100, 20, 100])
        
        layout.add_widget(Label(text="Bienvenido", font_size='24sp', size_hint_y=None, height=50))
        layout.add_widget(Button(text="Ir a Malla Curricular", size_hint=(None, None), size=(250, 60), on_release=self.ir_a_malla))
        
        self.add_widget(layout)

    def ir_a_malla(self, instance):
        self.manager.current = 'malla_curricular'
        
class MallaCurricularScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=20, padding=[20, 20, 20, 20])
        layout.add_widget(Label(text="Malla Curricular", font_size='24sp', size_hint_y=None, height=50))

        # ScrollView para las materias
        scroll = ScrollView(size_hint=(1, None), size=(Window.width, Window.height * 0.8))
        materias_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10, padding=[10, 10])
        materias_layout.bind(minimum_height=materias_layout.setter('height'))

        # Leer materias desde MongoDB agrupadas por semestre
        semestres = db.materias.aggregate([
            {"$group": {"_id": "$semestre", "materias": {"$push": "$nombre"}}},
            {"$sort": {"_id": 1}}
        ])

        for semestre in semestres:
            semestre_id = semestre["_id"] if semestre["_id"] else "Sin nombre"
            materias_layout.add_widget(Label(text=str(semestre_id), font_size='20sp', bold=True, size_hint_y=None, height=40))
            for materia in semestre["materias"]:
                materia_nombre = materia if materia else "Materia desconocida"
                materias_layout.add_widget(
                    Button(text=str(materia_nombre), size_hint_y=None, height=50, on_release=self.seleccionar_materia)
                )
        
        scroll.add_widget(materias_layout)
        layout.add_widget(scroll)
        layout.add_widget(Button(text="Salir", size_hint=(None, None), size=(200, 50), on_release=self.salir))
        self.add_widget(layout)

    def seleccionar_materia(self, instance):
        print(f"Materia seleccionada: {instance.text}")
        self.manager.current = 'temario'
        self.manager.get_screen('temario').cargar_temas(instance.text)

    def salir(self, instance):
        self.manager.current = 'inicio'

class TemarioScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', spacing=20, padding=[20, 20, 20, 20])
        self.temas_checkbox = []
        self.add_widget(self.layout)

    def cargar_temas(self, materia):
        self.layout.clear_widgets()
        self.materia = materia.strip()
        self.layout.add_widget(Label(text=f"Temario de {materia if materia else 'Sin nombre'}", font_size='24sp', size_hint_y=None, height=50))

        scroll = ScrollView(size_hint=(1, 1))
        temas_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10, padding=[10, 10])
        temas_layout.bind(minimum_height=temas_layout.setter('height'))

        # Leer temas desde MongoDB
        try:
            temas = db.materias.find_one({"nombre": self.materia})
            print(f"Resultado de la consulta para '{self.materia}': {temas}")  # Mensaje para depuración

            # Verificar si los datos son válidos
            if temas and "temas" in temas and isinstance(temas["temas"], list):
                temas_list = temas["temas"]
                for tema in temas_list:
                    if "numero" in tema and "titulo" in tema:
                        tema_text = f"{tema['numero']}. {tema['titulo']}" if tema['numero'] else tema['titulo']
                    else:
                        tema_text = "Título desconocido"

                    # Crear una fila con Checkbox y etiqueta para cada tema
                    tema_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)

                    checkbox = CheckBox(size_hint=(None, None), size=(50, 50))
                    tema_label = Label(text=tema_text, size_hint_x=1)
                    
                    tema_layout.add_widget(checkbox)
                    tema_layout.add_widget(tema_label)

                    self.temas_checkbox.append((checkbox, tema_text))  # Guardar para obtener los seleccionados después
                    temas_layout.add_widget(tema_layout)

            else:
                print("No se encontraron temas o la estructura de datos no es válida.")
                temas_layout.add_widget(Label(text="No hay temas disponibles", size_hint=(1, None), height=40))

        except Exception as e:
            print(f"Error al consultar MongoDB: {e}")
            temas_layout.add_widget(Label(text="Error al cargar los temas", size_hint=(1, None), height=40))

        scroll.add_widget(temas_layout)
        self.layout.add_widget(scroll)

        # Añadir botones para generar resumen, guía de estudio, y conectarse con el bot
        botones_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        botones_layout.add_widget(Button(text="Generar Resumen", size_hint=(None, None), size=(200, 50), on_release=self.generar_resumen_pdf))
        botones_layout.add_widget(Button(text="Generar Guía de Estudio", size_hint=(None, None), size=(200, 50), on_release=self.generar_guia_pdf))
        botones_layout.add_widget(Button(text="Generar Resumen con Bot", size_hint=(None, None), size=(200, 50), on_release=self.redirigir_al_bot))
        botones_layout.add_widget(Button(text="Generar Guía con Bot", size_hint=(None, None), size=(200, 50), on_release=self.redirigir_al_bot))

        self.layout.add_widget(botones_layout)
        self.layout.add_widget(Button(text="Salir", size_hint=(None, None), size=(200, 50), on_release=self.salir))

    def obtener_temas_seleccionados(self):
        return [tema_text for checkbox, tema_text in self.temas_checkbox if checkbox.active]

    def generar_resumen_pdf(self, instance):
        temas = self.obtener_temas_seleccionados()
        if temas:
            temas_combinados = "; ".join(temas)
            resumen = self.generar_resumen_openai(temas_combinados)
            self.crear_pdf(resumen, "resumen.pdf")
        else:
            self.mostrar_resultado("Por favor, selecciona al menos un tema.", "Error")

    def generar_guia_pdf(self, instance):
        temas = self.obtener_temas_seleccionados()
        if temas:
            temas_combinados = "; ".join(temas)
            guia = self.generar_preguntas_openai(temas_combinados)
            self.crear_pdf(guia, "guia_estudio.pdf")
        else:
            self.mostrar_resultado("Por favor, selecciona al menos un tema.", "Error")

    def crear_pdf(self, contenido, nombre_archivo):
        c = canvas.Canvas(nombre_archivo, pagesize=letter)
        c.drawString(100, 750, "Guía de Estudio")
        c.drawString(100, 730, contenido)
        c.save()
        print(f"PDF generado: {nombre_archivo}")

    def redirigir_al_bot(self, instance):
        # Reemplaza por la URL de tu bot de Telegram
        webbrowser.open("https://t.me/beeDICIS_bot")

    def generar_resumen_openai(self, temas):
        try:
            respuesta = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un asistente que ayuda a generar resúmenes sobre temas educativos."},
                    {"role": "user", "content": f"Genera un resumen sobre los siguientes temas: {temas}"}
                ],
                max_tokens=300
            )
            return respuesta.choices[0].message['content'].strip()
        except Exception as e:
            print(f"Error al generar el resumen con OpenAI: {e}")
            return "Lo siento, hubo un error al generar el resumen. Por favor, inténtalo de nuevo más tarde."

    def generar_preguntas_openai(self, temas):
        try:
            respuesta = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un asistente que genera preguntas para guiar el estudio de temas específicos."},
                    {"role": "user", "content": f"Genera 5 preguntas importantes para estudiar los siguientes temas: {temas}"}
                ],
                max_tokens=200
            )
            return respuesta.choices[0].message['content'].strip()
        except Exception as e:
            print(f"Error al generar las preguntas con OpenAI: {e}")
            return "Lo siento, hubo un error al generar las preguntas. Por favor, inténtalo de nuevo más tarde."

    def mostrar_resultado(self, resultado, titulo):
        self.manager.get_screen('tema_detalle').cargar_detalle(self.materia, resultado)
        self.manager.current = 'tema_detalle'

    def salir(self, instance):
        self.manager.current = 'malla_curricular'

class TemaDetalleScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', spacing=20, padding=[20, 20, 20, 20])
        self.add_widget(self.layout)

    def cargar_detalle(self, materia, tema):
        self.layout.clear_widgets()
        self.layout.add_widget(Label(text=f"Resumen del tema: {tema}", font_size='24sp', size_hint_y=None, height=50))

        # Generar resumen usando OpenAI
        prompt = f"Por favor, proporciona un resumen detallado sobre el tema '{tema}' de la materia '{materia}'."

        try:
            # Usar la versión actualizada de la API para obtener el resumen
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un asistente que proporciona resúmenes académicos."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150
            )
            resumen = response['choices'][0]['message']['content'].strip()
        except Exception as e:
            resumen = f"Error al generar el resumen: {str(e)}"

        # Mostrar el resumen generado
        self.layout.add_widget(Label(text=resumen, font_size='18sp', size_hint_y=None, height=200))

        # Botón para regresar
        self.layout.add_widget(Button(text="Regresar", size_hint=(None, None), size=(200, 50), on_release=self.salir))

    def salir(self, instance):
        self.manager.current = 'temario'

class MainApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(InicioScreen(name='inicio'))
        sm.add_widget(MallaCurricularScreen(name='malla_curricular'))
        sm.add_widget(TemarioScreen(name='temario'))
        sm.add_widget(TemaDetalleScreen(name='tema_detalle'))
        return sm


if __name__ == "__main__":
    MainApp().run()


import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from dotenv import load_dotenv
import os
import openai

# Carga las variables de entorno
load_dotenv()

# Configura el logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Obtén el token del bot y la clave de OpenAI desde las variables de entorno
TOKEN_BOT = os.getenv('TOKEN_BOT')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Configura la clave de API de OpenAI
openai.api_key = OPENAI_API_KEY

# Función para generar resumen usando la API de OpenAI
def generar_resumen(temas):
    try:
        if len(temas) > 2000:
            return "El texto es demasiado largo. Por favor, intenta resumirlo."
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
        logging.error(f"Error al generar resumen: {e}")
        return "Error al generar el resumen. Inténtalo más tarde."

# Función para generar guía de estudio usando la API de OpenAI
def generar_guia(temas):
    try:
        if len(temas) > 2000:
            return "El texto es demasiado largo. Por favor, intenta resumirlo."
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
        logging.error(f"Error al generar guía: {e}")
        return "Error al generar la guía de estudio. Inténtalo más tarde."

# Función para manejar preguntas o peticiones adicionales usando la API de OpenAI
def responder_pregunta(peticion):
    try:
        if len(peticion) > 2000:
            return "El texto es demasiado largo. Por favor, intenta resumirlo."
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
        logging.error(f"Error al responder la pregunta: {e}")
        return "Error al procesar tu petición. Inténtalo más tarde."

# Comando /start
async def start(update: Update, context) -> None:
    logging.info(f"/start ejecutado por {update.effective_user.username}")

    keyboard = [
        [InlineKeyboardButton("Generar Resumen", callback_data="generar_resumen")],
        [InlineKeyboardButton("Generar Guía de Estudio", callback_data="generar_guia")],
        [InlineKeyboardButton("Hacer una Pregunta", callback_data="hacer_pregunta")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "¡Hola! Soy tu asistente educativo. Puedes usar los comandos o seleccionar una opción:\n"
        "/resumen - Generar un resumen\n"
        "/guia - Crear una guía de estudio\n"
        "/pregunta - Hacer una pregunta o petición",
        reply_markup=reply_markup
    )

# Comando /resumen
async def resumen(update: Update, context) -> None:
    logging.info(f"/resumen ejecutado por {update.effective_user.username}")
    await update.message.reply_text("Por favor, envíame los temas para generar el resumen.")
    context.user_data['action'] = 'resumen'

# Comando /guia
async def guia(update: Update, context) -> None:
    logging.info(f"/guia ejecutado por {update.effective_user.username}")
    await update.message.reply_text("Por favor, envíame los temas para generar la guía de estudio.")
    context.user_data['action'] = 'guia'

# Comando /pregunta
async def pregunta(update: Update, context) -> None:
    logging.info(f"/pregunta ejecutado por {update.effective_user.username}")
    await update.message.reply_text("Por favor, envíame tu pregunta o petición.")
    context.user_data['action'] = 'pregunta'

# Manejar botones de resumen, guía y preguntas
async def handle_callback(update: Update, context) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "generar_resumen":
        await query.edit_message_text("Por favor, envíame los temas para generar el resumen.")
        context.user_data['action'] = 'resumen'
    elif query.data == "generar_guia":
        await query.edit_message_text("Por favor, envíame los temas para generar la guía de estudio.")
        context.user_data['action'] = 'guia'
    elif query.data == "hacer_pregunta":
        await query.edit_message_text("Por favor, envíame tu pregunta o petición.")
        context.user_data['action'] = 'pregunta'

# Manejar mensajes de texto para generar contenido o responder preguntas
async def handle_text(update: Update, context) -> None:
    user_action = context.user_data.get('action')

    if not user_action:
        await update.message.reply_text("Por favor, selecciona una opción usando /start antes de enviar un mensaje.")
        return

    if user_action == 'resumen':
        temas = update.message.text
        resumen = generar_resumen(temas)
        await update.message.reply_text(f"✅ Resumen generado:\n\n{resumen}")
    elif user_action == 'guia':
        temas = update.message.text
        guia = generar_guia(temas)
        await update.message.reply_text(f"📘 Guía de estudio generada:\n\n{guia}")
    elif user_action == 'pregunta':
        peticion = update.message.text
        respuesta = responder_pregunta(peticion)
        await update.message.reply_text(f"🤖 Respuesta:\n\n{respuesta}")

    context.user_data['action'] = None  # Reiniciar acción del usuario

# Manejar errores
async def error_handler(update: Update, context) -> None:
    logging.error(msg="Excepción mientras se manejaba una actualización:", exc_info=context.error)
    if update:
        await update.message.reply_text("Ocurrió un error inesperado. Por favor, intenta de nuevo más tarde.")

# Configura el bot
if __name__ == '__main__':
    if not TOKEN_BOT or not OPENAI_API_KEY:
        logging.error("El token del bot o la clave de OpenAI no están configurados.")
        exit(1)

    application = ApplicationBuilder().token(TOKEN_BOT).build()

    # Añade los manejadores de comandos y mensajes
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("resumen", resumen))
    application.add_handler(CommandHandler("guia", guia))
    application.add_handler(CommandHandler("pregunta", pregunta))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Añade el manejador de errores
    application.add_error_handler(error_handler)

    # Inicia el bot
    logging.info("El bot se está ejecutando...")
    application.run_polling()

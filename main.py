from telegram import Update, InlineKeyboardButton,InlineKeyboardMarkup,ReplyKeyboardMarkup
from telegram.ext import  MessageReactionHandler,ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, \
    CallbackContext,ConversationHandler,Application,CallbackQueryHandler, ExtBot
import logging
import os
from dotenv import load_dotenv
import product_management
import database
import admin
import users
load_dotenv()
TOKEN = os.getenv("TOKEN")
ADMIN = os.getenv("ADMIN")

app = Application.builder().token(TOKEN).build()
ExtBot.initialize(app.bot)

logging.basicConfig(

    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO

)



# set higher logging level for httpx to avoid all GET and POST requests being logged

logging.getLogger("httpx").setLevel(logging.WARNING)


logger = logging.getLogger(__name__)




async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    database.save_user(update.effective_user.id, update.effective_user.username, update.effective_user.first_name)
    keyboard = [["مشاهده سبد خرید"]]
    if str(update.effective_user.id) == ADMIN:
        await update.message.reply_text(f"سلام ادمین {update.effective_user.first_name}!\nبه ربات مدیریت فروشگاه خوش آمدید.")
        await admin.admin_panel(update, context)
    else:
        await update.message.reply_text(f"سلام {update.effective_user.first_name}!\nبه ربات فروشگاه خوش آمدید.", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        await users.user_panel(update, context)


def main():
    
    
    app.add_handler(CommandHandler("start", start))    
    
    app.add_handler(product_management.add_product_conv_handler)
    app.add_handler(product_management.delete_product_conv_handler)
    app.add_handler(product_management.edit_product_conv_handler)
    app.add_handler(product_management.all_products)   
    app.add_handler(CallbackQueryHandler(admin.choose))

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
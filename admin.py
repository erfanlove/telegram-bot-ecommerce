from telegram import Update, InlineKeyboardButton,InlineKeyboardMarkup
from telegram.ext import  MessageReactionHandler,ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, \
    CallbackContext,ConversationHandler,Application,CallbackQueryHandler
import logging
import os
from dotenv import load_dotenv
import database
import admin
import users
import product_management
import uuid
MANAGEPRODUCTS, VIEWORDERS, VIEWUSERS = range(3)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton("مشاهده کاربران", callback_data=str(VIEWUSERS)),
            InlineKeyboardButton("مدیریت محصولات", callback_data=str(MANAGEPRODUCTS)),
        ],
        [
            InlineKeyboardButton("مشاهده سفارشات", callback_data=str(VIEWORDERS)),
        ],
    ]
    replay_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("پنل ادمین:\nلطفا یکی از گزینه های زیر را انتخاب کنید", reply_markup=replay_markup)
    
async def choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("admin choose called")
    query = update.callback_query
    await query.answer()
    choice = query.data
    if choice == str(MANAGEPRODUCTS):
        await product_management.manage_products(update, context)
    else:
        await query.edit_message_text(text="این بخش در حال حاضر در دسترس نیست.")



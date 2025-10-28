from telegram import Update, InlineKeyboardButton,InlineKeyboardMarkup,ReplyKeyboardMarkup
from telegram.ext import  MessageReactionHandler,ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, \
    CallbackContext,ConversationHandler,Application,CallbackQueryHandler
import logging
import os
from main import app
from dotenv import load_dotenv
import database
import admin
import users
import product_management
import uuid
load_dotenv()

ADMIN = os.getenv("ADMIN")

CHECKOUT, AWAITING_PAYMENT, QUANTITY, DELETE_ORDER = range(4)

async def user_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("سفارشات من", callback_data='my_orders'),
         InlineKeyboardButton("ارتباط با پشتیبانی", callback_data='contact_support')],
         [InlineKeyboardButton("لیست محصولات", callback_data='product_list'),
          InlineKeyboardButton("مشاهده سبد خرید", callback_data='view_cart')],
         
    ]
    replay_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("\nلطفا یکی از گزینه های زیر را انتخاب کنید", reply_markup=replay_markup)
    
    
async def products_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("last products called")
    
    query = update.callback_query
    await query.answer()
    products = database.products_list()
    if not products:
        await query.edit_message_text(text="هیچ محصولی یافت نشد.")
        return
    
    for product in products:
        keyboard = [
        [InlineKeyboardButton("اضافه کردن به سبد خرید", callback_data=str(product._id))],
        ]
        replay_markup = InlineKeyboardMarkup(keyboard)
        message = f"نام: {product[1]}\nتوضیحات: {product[2]}\nقیمت: {product[3]}\n\n"
        await update.effective_message.reply_photo(photo=product[4], caption=message, reply_markup=replay_markup)
        
        
async def choose_quantity(update: Update,context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.user_data['product_id'] = query.data
    await query.answer()
    await query.edit_message_text(text="لطفا تعداد مورد نظر را وارد کنید:")
    return QUANTITY
        
async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['quantity'] = update.effective_message.text
    query = update.callback_query
    user = database.get_user_by_telegramid(update.effective_user.id)
    database.add_to_cart(user_id=user, product_id=context.user_data['product_id'], quantity=context.user_data['quanntity'], status="in_cart")
    await query.answer()
    await query.edit_message_text(text="محصول به سبد خرید اضافه شد.")
    
async def delete_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = database.get_user_by_telegramid(update.effective_user.id)
    database.delete_order(user_id=user)
    await query.edit_message_text(text="سفارش شما حذف شد.")

async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = database.get_user_by_telegramid(update.effective_user.id)
    orders = database.get_orders_by_user(user_id=user)
    if not orders:
        await query.edit_message_text(text="شما هیچ سفارشی ندارید.")
        return
    message = "سفارشات شما:\n\n"
    keyboard = [
        [InlineKeyboardButton("نهایی کردن سفارش", callback_data='checkout')],
        [InlineKeyboardButton("حذف سفارش", callback_data='delete_order')],
    ]
    replay_markup = InlineKeyboardMarkup(keyboard)
    for order in orders:
        message += f"نام محصول: {order.product.name}\nتعداد: {order.quantity}\nوضعیت: {order.status}\n\n"
    await query.edit_message_text(text=message, reply_markup=replay_markup)

async def checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="لطفا فیش واریزی خود را ارسال کنید.")
    return AWAITING_PAYMENT

async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("فیش واریزی شما دریافت شد. پس از بررسی سفارش شما تایید خواهد شد.")
    await app.bot.send_photo(chat_id=ADMIN, photo=update.message.photo[-1].file_id, caption=f"فیش واریزی از طرف {update.effective_user.first_name} {update.effective_user.last_name} (@{update.effective_user.username})")
    return ConversationHandler.END
    
add_to_cart_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(choose_quantity, pattern='^\d+$')],
    states={
        QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_to_cart)],
    },
    fallbacks=[],
)

veiw_cart_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(my_orders, pattern='^view_cart$')],
    states={DELETE_ORDER: [CallbackQueryHandler(delete_order, pattern='^delete_order$')],
            CHECKOUT: [CallbackQueryHandler(checkout, pattern='^checkout$')],
            AWAITING_PAYMENT: [MessageHandler(filters.PHOTO, process_payment)],},
    fallbacks=[],
)


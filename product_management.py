from telegram import Update, InlineKeyboardButton,InlineKeyboardMarkup,ReplyKeyboardMarkup,ReplyKeyboardRemove
from telegram.ext import  MessageReactionHandler,ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, \
    CallbackContext,ConversationHandler,Application,CallbackQueryHandler
import logging
import os
from dotenv import load_dotenv
import database
import uuid
from main import app

ADDPRODUCT, EDITPRODUCT, DELETEPRODUCT, VIEWALLPRODUCTS = range(3,7)
RECEIVENAMED, RECEIVEPRICED, RECEIVEDESCRIPTIOND, RECEIVEIMAGED = range(7, 11)
SELECTEDEDIT ,EDITNAME, EDITPRICE, EDITDESCRIPTION, EDITIMAGE = range(11, 16)
DELETINGPRODUCT,CONFIRMDELETE = range(16, 18)


async def view_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = database.Session()
    users = session.query(database.User).all()
    if users:
        message = "لیست کاربران:\n"
        for user in users:
            message += f"نام: {user.first_name}\nآیدی تلگرام: {user.telegramid}\nنام کاربری: @{user.username}\n\n"
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("هیچ کاربری موجود نیست.")
    session.close()


async def view_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = database.Session()
    orders = session.query(database.Order).all()
    if orders:
        message = "لیست سفارشات:\n"
        for order in orders:
            user = session.query(database.User).filter_by(_id=order.user_id).first()
            product = session.query(database.Product).filter_by(_id=order.product_id).first()
            message += f"کاربر: {user.first_name} (ID: {user.telegramid})\nمحصول: {product.name}\nتعداد: {order.quantity}\nوضعیت: {order.status}\n\n"
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("هیچ سفارشی موجود نیست.")
    session.close()
    
async def manage_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("افزودن محصول جدید", callback_data=str(ADDPRODUCT))],
        [InlineKeyboardButton("ویرایش محصول", callback_data=str(EDITPRODUCT))],
        [InlineKeyboardButton("حذف محصول", callback_data=str(DELETEPRODUCT))],
        [InlineKeyboardButton("مشاهده همه محصولات", callback_data= str(VIEWALLPRODUCTS))],
    ]
    replay_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="مدیریت محصولات:\nلطفا یکی از گزینه های زیر را انتخاب کنید", reply_markup=replay_markup)
        
      
#ADDING NEW PRODUCT  
        
async def new_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Adding new product")
    query = update.callback_query
    await query.answer()
    print("Callback query answered")
    print(query.data)
    await query.edit_message_text(text="( /cancel ) لطفا نام محصول را وارد کنید:")
    print("Asked for product name")
    
    return RECEIVENAMED  # مرحله بعدی برای دریافت نام محصول

async def receive_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Receiving product name")
    context.user_data['product_name'] = update.effective_message.text
    print(context.user_data['product_name'])
    await update.effective_message.reply_text("( /cancel ) لطفا قیمت محصول را وارد کنید:")
    return RECEIVEPRICED  # مرحله بعدی برای دریافت قیمت محصول

async def receive_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['product_price'] = update.message.text
    await update.effective_message.reply_text("( /cancel ) لطفا توضیحات محصول را وارد کنید:")
    return RECEIVEDESCRIPTIOND  # مرحله بعدی برای دریافت توضیحات محصول

async def receive_product_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['product_description'] = update.message.text
    await update.effective_message.reply_text("( /cancel ) لطفا تصویر محصول را ارسال کنید:")
    return RECEIVEIMAGED  # مرحله بعدی برای دریافت تصویر محصول

async def receive_product_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_message.photo:
        # ذخیره تصویر محصول
        file_name = str(uuid.uuid4()) + ".jpg"
        photo_file = await update.effective_message.photo[-1].get_file()
        image_path = f"images/{file_name}"
        os.makedirs("images", exist_ok=True)
        await photo_file.download_to_drive(image_path)
        
        # ذخیره محصول در دیتابیس
        new_product = database.Product(
            name=context.user_data['product_name'],
            price=context.user_data['product_price'],
            description=context.user_data['product_description'],
            image=image_path
        )
        session = database.Session()
        session.add(new_product)
        session.commit()
        session.close()
        
        await update.effective_message.reply_text("محصول با موفقیت اضافه شد!")
    else:
        await update.effective_message.reply_text("لطفا یک تصویر معتبر ارسال کنید.")
    
    return ConversationHandler.END  # پایان گفتگو

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("عملیات لغو شد.")
    return ConversationHandler.END  # پایان گفتگو

#END ADDING NEW PRODUCT

#START EDIT PRODUCT
async def find_to_edit_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = database.Session()
    products = session.query(database.Product).all()
    if products:
        keyboard = []
        for product in products:
            keyboard.append([InlineKeyboardButton(product.name, callback_data=product._id)])
        replay_markup = InlineKeyboardMarkup(keyboard)
        await update.effective_message.reply_text("لطفا محصولی برای ویرایش انتخاب کنید:", reply_markup=replay_markup)
        return SELECTEDEDIT  # مرحله بعدی برای ویرایش محصول
        
    else:
        await update.message.reply_text("هیچ محصولی موجود نیست.")
    session.close()

async def edit_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_id = int(query.data)
    session = database.Session()
    product = session.query(database.Product).filter_by(_id=product_id).first()
    if product:
        context.user_data['edit_product_id'] = product_id
        await query.edit_message_text(text=f"شما در حال ویرایش محصول '{product.name}' هستید.\nلطفا نام جدید محصول را وارد کنید: \n ( /cancel )")
        return EDITNAME  # مرحله بعدی برای دریافت نام جدید محصول   
    else:
        await query.edit_message_text(text="محصول مورد نظر یافت نشد.")
        session.close()
        return ConversationHandler.END  # پایان گفتگو

async def receive_new_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_product_name'] = update.message.text
    await update.message.reply_text(" ( /cancel ) لطفا قیمت جدید محصول را وارد کنید:")
    return EDITPRICE  # مرحله بعدی برای دریافت قیمت جدید محصول

async def receive_new_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_product_price'] = update.message.text
    await update.message.reply_text(" ( /cancel ) لطفا توضیحات جدید محصول را وارد کنید:")
    return EDITDESCRIPTION  # مرحله بعدی برای دریافت توضیحات جدید محصول

async def receive_new_product_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_product_description'] = update.message.text
    await update.message.reply_text(" ( /cancel ) لطفا تصویر جدید محصول را ارسال کنید:")
    return EDITIMAGE  # مرحله بعدی برای دریافت تصویر جدید محصول

async def receive_new_product_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        product_id = context.user_data['edit_product_id']
        session = database.Session()
        product = session.query(database.Product).filter_by(_id=product_id).first()
        previous_photo = session.query(database.Product).filter_by(_id=product_id).first().image
        if previous_photo and os.path.exists(previous_photo):
            os.remove(previous_photo)  # حذف تصویر قبلی
        if product:
            # ذخیره تصویر جدید محصول
            file_name = str(uuid.uuid4()) + ".jpg"
            photo_file = await update.message.photo[-1].get_file()
            image_path = f"images/{file_name}"
            os.makedirs("images", exist_ok=True)
            await photo_file.download_to_drive(image_path)
            
            # به‌روزرسانی اطلاعات محصول در دیتابیس
            product.name = context.user_data['new_product_name']
            product.price = context.user_data['new_product_price']
            product.description = context.user_data['new_product_description']
            product.image = image_path
            
            session.commit()
            await update.message.reply_text("محصول با موفقیت ویرایش شد!")
        else:
            await update.message.reply_text("محصول مورد نظر یافت نشد.")
        session.close()
    else:
        await update.message.reply_text("لطفا یک تصویر معتبر ارسال کنید.")
    
    return ConversationHandler.END  # پایان گفتگو

#END EDIT PRODUCT
#START DELETE PRODUCT
    
async def find_to_delete_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = database.Session()
    products = session.query(database.Product).all()
    if products:
        keyboard = []
        for product in products:
            keyboard.append([InlineKeyboardButton(product.name, callback_data=product._id)])
        replay_markup = InlineKeyboardMarkup(keyboard)
        await update.effective_message.reply_text("لطفا محصولی برای حذف انتخاب کنید:", reply_markup=replay_markup)
        return CONFIRMDELETE  # مرحله بعدی برای حذف محصول   
    else:
        await update.message.reply_text("هیچ محصولی موجود نیست.")
        session.close()
        return ConversationHandler.END  # پایان گفتگو
    
    
    
async def confirm_delete_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_id = int(query.data)
    context.user_data['delete_product_id'] = product_id
    session = database.Session()
    product = session.query(database.Product).filter_by(_id=product_id).first()
    if product:
        keyboard = [
            [
                InlineKeyboardButton("بله", callback_data=str(product_id)),
                InlineKeyboardButton("خیر", callback_data='cancel_delete'),
            ]
        ]
        replay_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=f"آیا مطمئن هستید که می‌خواهید محصول '{product.name}' را حذف کنید؟", reply_markup=replay_markup)
        session.close()
        return DELETINGPRODUCT  # مرحله بعدی برای حذف محصول   
    else:
        await query.edit_message_text(text="محصول مورد نظر یافت نشد.")
        session.close()
        return ConversationHandler.END  # پایان گفتگو
    
    
async def delete_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_id = int(query.data)
    session = database.Session()
    product = session.query(database.Product).filter_by(_id=product_id).first()
    if product:
        session.delete(product)
        session.commit()
        await query.edit_message_text(text=f"محصول '{product.name}' با موفقیت حذف شد. ( /cancel )")
        session.close()
        return ConversationHandler.END  # پایان گفتگو   
    else:
        await query.edit_message_text(text="محصول مورد نظر یافت نشد.")
    session.close()
    return ConversationHandler.END  # پایان گفتگو   
#END DELETE PRODUCT

async def show_all_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = database.Session()
    products = session.query(database.Product).all()
    if products:
        await update.effective_message.reply_text("محصولات موجود:")
        for product in products:
            await update.effective_message.reply_photo(photo=open(product.image, 'rb'), caption=f"نام: {product.name}\nقیمت: {product.price}\nتوضیحات: {product.description}")
        
    else:
        await update.effective_message.reply_text("هیچ محصولی موجود نیست.")
    session.close()
    

add_product_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(new_product, pattern="^"+str(ADDPRODUCT)+"$")],
    states={
        RECEIVENAMED: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_product_name)],
        RECEIVEPRICED: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_product_price)],
        RECEIVEDESCRIPTIOND: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_product_description)],
        RECEIVEIMAGED: [MessageHandler(filters.PHOTO, receive_product_image)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)
# اضافه کردن conv_handler به اپلیکیشن در main.py

edit_product_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(find_to_edit_product, pattern="^"+str(EDITPRODUCT)+"$")],
    states={
        SELECTEDEDIT: [CallbackQueryHandler(edit_product)],
        EDITNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_new_product_name)],
        EDITPRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_new_product_price)],
        EDITDESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_new_product_description)],
        EDITIMAGE: [MessageHandler(filters.PHOTO, receive_new_product_image)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)

delete_product_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(find_to_delete_product, pattern='^'+str(DELETEPRODUCT)+'$')],
    states={
        CONFIRMDELETE: [CallbackQueryHandler(confirm_delete_product)],
        DELETINGPRODUCT: [CallbackQueryHandler(delete_product)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)


all_products = CallbackQueryHandler(show_all_products, pattern="^"+str(VIEWALLPRODUCTS)+"$")
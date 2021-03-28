#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import os
from pprint import pprint
from subprocess import run
from datetime import datetime

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

from ImageEngine import *

# Enable logging
logging.basicConfig(
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
	"""Send a message when the command /start is issued."""
	update.message.reply_text('hi!!!')

def shutdown_command(update, context):
	"""shutdown the bot process"""
	if update.effective_user.id != 227093322:
		return
	update.message.reply_text(str(os.getpid()) + " will shutdown")
	os.kill(os.getpid(), 2)

def help_command(update, context):
	"""Send a message when the command /help is issued."""
	update.message.reply_text('send image dumb ape!')

def process_command(update, context):
	pass
	
def get_command(update, context):
	if update.message.reply_to_message is None or len(update.message.reply_to_message.photo) == 0:
		update.message.reply_text("to get HiRes image, reply to a LowRes image with the /get command")
		return
	if update.message.reply_to_message.document != None:
		update.message.reply_text("that image is already HiRes")
	pprint(update.message.reply_to_message.photo[0].get_file().file_path)
		

def pano_command(update, context):
	update.message.reply_text('start sending images and send \'end\' to stop and process')
	return 'getimg'

def pano_image_recieve(update, context):
	if update.message.document is None:
		file=update.message.photo[-1].get_file()
	else:
		file=update.message.document.get_file()
	path="img/" + str(file.file_unique_id)+".jpg"
	file.download(custom_path=path)
	if 'pano' in context.chat_data:
		context.chat_data['pano'] += [path]
	else:
		context.chat_data['pano'] = [path]
	update.message.reply_text("got " + str(len(context.chat_data['pano'])) + " image")

def process_pano(update, context):
	update.message.reply_text("now wait")
	outName="img/" + context.chat_data['pano'][0][4:]+'-'+context.chat_data['pano'][-1][4:]+'.jpg'
	ptoName="img/" + context.chat_data['pano'][0][4:]+'-'+context.chat_data['pano'][-1][4:]+'.pto'
	imgs=' '.join(context.chat_data['pano'])
	log=""
	"""log+=run(['pto_gen', *context.chat_data['pano'], '-o', ptoName], capture_output=True,text=True).stdout
	log+=run(['hugin_executor', '-a', ptoName], capture_output=True,text=True).stdout
	log+=run(['pano_modify', '--ldr-file=JPG', ptoName, '-o', ptoName], capture_output=True,text=True).stdout
	log+=run(['hugin_executor', '-p', outName, '-s', ptoName], capture_output=True,text=True).stdout
	"""
	with open("mkPano.sh", 'r') as f:
		coms=f.readlines()
	for com in coms:
		comStr = com.replace("%outPto", ptoName).replace("%imgs", imgs).replace("%outImg", outName)
		log+="*******************************\n"+comStr+"\n*******************************\n"
		log+=run(comStr.strip().split(' '), capture_output=True,text=True).stdout
	logn=str(datetime.now())+".log"
	with open(logn, "w") as f:
		f.write(log)
	with open(logn, "rb") as f:
		update.message.reply_document(f)
	try:
		with open(outName, 'rb') as f:
			update.message.reply_photo(f)
			f.seek(0)
			update.message.reply_document(f)
		update.message.reply_text("there you go!")
	except Exception as e:
		print(e)
		update.message.reply_text("couldn't make the pano")
	context.chat_data['pano']=[]
	return ConversationHandler.END
	
def on_image_recieve(update, context):
	"""saves a file id and name to file"""
	if update.message.document is None:
		file=update.message.photo[-1].get_file()
	else:
		file=update.message.document.get_file()
	path="img/" + str(file.file_unique_id)+".jpg"
	file.download(custom_path=path)
	update.message.reply_text("got it")
	Lpath=supper_res(path) #path[:-4]+"_Large.jpg"
	megaPixels=float(run(["exiftool", "-s", "-s", "-s", "-Megapixels", path], capture_output=True,text=True).stdout)
	if megaPixels<=0.5: scale=6
	elif megaPixels<=2: scale=4
	elif megaPixels<=4: scale=4
	else: scale=2
	update.message.reply_text("enlarging your image "+str(scale)+" times!")
	#gmic img/AQADDZV9J10AAxpgBgAB.jpg -scale_dcci2x ,,, -output out.jpg
	#run(['gmic', path, '-repeat', str(scale/2), '-scale_dcci2x', ',', '-done', '-output', Lpath])
	#run(['convert', path, "-filter", "Lanczos", "-distort", "Resize", str(scale*100)+"%", "-unsharp", "0", Lpath])
	try:
		with open(Lpath, 'rb') as f:
			update.message.reply_document(f)
		update.message.reply_text("here is the image magnified by "+str(scale)+"!")
	except Exception as e:
		print(e)
		update.message.reply_text("image could not be magnified")
	#classify_image()

def main():
	"""Start the bot."""
	run(["mkdir", "img"])
	with open("tk", 'r') as tk:
		updater = Updater(tk.read()[:-1], use_context=True)

	# Get the dispatcher to register handlers
	dp = updater.dispatcher

	# on different commands - answer in Telegram
	dp.add_handler(CommandHandler("start", start))
	dp.add_handler(CommandHandler("help", help_command))
	dp.add_handler(CommandHandler("get", get_command))
	dp.add_handler(CommandHandler("shutdown", shutdown_command))
	dp.add_handler(CommandHandler("process", process_command))

	conv_handler = ConversationHandler(
		entry_points=[CommandHandler("pano", pano_command)],
		states={
			'getimg': [MessageHandler(Filters.document.image | Filters.photo & ~Filters.command, pano_image_recieve), MessageHandler(Filters.text, process_pano)]
		},
		fallbacks=[],
		allow_reentry=True
	)
	dp.add_handler(conv_handler)
	dp.add_handler(MessageHandler(Filters.document.image | Filters.photo & ~Filters.command, on_image_recieve))

	# Start the Bot
	updater.start_polling()

	# Run the bot until you press Ctrl-C or the process receives SIGINT,
	# SIGTERM or SIGABRT. This should be used most of the time, since
	# start_polling() is non-blocking and will stop the bot gracefully.
	updater.idle()


if __name__ == '__main__':
	main()

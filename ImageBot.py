#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import os
import io
from pprint import pprint
from subprocess import run
from datetime import datetime
from cv2 import imwrite, imencode

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, PicklePersistence

from ImageEngine import *

# Enable logging
logging.basicConfig(
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

def saveImage(update, context=None):
	if update.message.document is None:
		file=update.message.photo[-1].get_file()
	else:
		file=update.message.document.get_file()
	path="img/" + str(file.file_unique_id)
	file.download(custom_path=path)
	return path

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
	update.message.reply_text('just type / to see the commands available')

def cancel_command(update, context):
	update.message.reply_text("the current action will be cancelled")
	return ConversationHandler.END

def get_command(update, context):
	if update.message.reply_to_message is None or len(update.message.reply_to_message.photo) == 0:
		update.message.reply_text("to get HiRes image, reply to a LowRes image with the /get command")
		return
	if update.message.reply_to_message.document != None:
		update.message.reply_text("that image is already HiRes")
	pprint(update.message.reply_to_message.photo[0].get_file().file_path)

"""def on_image_recieve(update, context):
	path=saveImage(update, context)
	update.message.reply_text("got it!")
	update.message.reply_text("now classifying...")
	ret = classify_image(path, context)
	if ret is None:
		update.message.reply_text("found nothing in this image😒")
		return
	img, faceNum, faces = ret
	update.message.reply_text("Found {0} faces!".format(faceNum))
	if len(faces)!=0:
		update.message.reply_text("There are {0} unidentified faces!".format(len(faces)))
		for face in faces:
			buff = imencode(".jpg", face)
			io_buf = io.BytesIO(buff[1])
			try: update.message.reply_photo(io_buf, caption="to add a name to this person reply to that image with the command /saveface")
			except Exception as e:
				print(e)
	buff = imencode(".jpg", img)
	io_buf = io.BytesIO(buff[1])
	try: update.message.reply_photo(io_buf)
	except Exception as e:
		print(e)
		update.message.reply_text("couldn't send as photo")
	io_buf.seek(0)
	update.message.reply_document(io_buf)
	update.message.reply_text("there you go!")"""

def on_image_recieve(update, context):
	img_path=saveImage(update, context)
	img_types = classify_image(img_path, context)
	if 'face' in img_types:
		faces, unknown_faces = img_types['face']
		if len(faces)>0:
			with open(img_path, 'rb') as image:
				update.message.reply_photo(image, caption=' '.join(['#'+face[1]+',' for face in faces]))
		if len(unknown_faces)>0:
			for face in unknown_faces:
				image = load_image_to_memory(face[0])
				update.message.reply_photo(image, caption="To save the name of that person reply to that image with the command /saveface")

###########################################
def pano_command(update, context):
	context.chat_data['pano']=[]
	update.message.reply_text('start sending images and send \'end\' to stop and process')
	return 'getimg'

def pano_image_recieve(update, context):
	path=saveImage(update, context)
	if 'pano' in context.chat_data:
		context.chat_data['pano'] += [path]
	else:
		context.chat_data['pano'] = [path]
	update.message.reply_text("got " + str(len(context.chat_data['pano'])) + " image")

def process_pano(update, context):
	update.message.reply_text("now wait")
	outName=context.chat_data['pano'][0]+'-'+context.chat_data['pano'][-1][4:]+'.jpg'
	#imgs=' '.join(context.chat_data['pano'])
	status=stitchImages(context.chat_data['pano'], outName)
	if status != 0:
		update.message.reply_text("could't make pano, exited with status code " + str(status))
		return ConversationHandler.END
	try:
		with open(outName, 'rb') as f:
			update.message.reply_document(f)
		update.message.reply_text("there you go!")
	except Exception as e:
		print(e)
		update.message.reply_text("couldn't make the pano")
	context.chat_data['pano']=[]
	return ConversationHandler.END
###########################################
#seamcarve
#gmic img/AQADDZV9J10AAxpgBgAB.jpg -seamcarve arg1,arg2,,, -output out.jpg
###########################################
def rescale_command(update, context):
	context.chat_data['rescale']=update.message.text
	update.message.reply_text('now send the image')
	return 'getimg'

def process_rescale(update, context):
	path=saveImage(update, context)
	update.message.reply_text("got it")
	Lpath=path+"_rescaled.jpg"
	update.message.reply_text("rescaling your image!")
	_, arg1, arg2 = context.chat_data['rescale'].split(' ')
	run(['convert', path, '-liquid-rescale', arg1+'x'+arg2+'%', Lpath])
	try:
		with open(Lpath, 'rb') as f:
			update.message.reply_document(f)
		update.message.reply_text("here is the rescaled image!")
	except Exception as e:
		print(e)
		update.message.reply_text("image could not be rescaled")
	return ConversationHandler.END
##########################################
#########################################
def cartoon_command(update, context):
	#context.chat_data['cartoon']=update.message.text
	update.message.reply_text('now send the image')
	return 'getimg'
	
def process_cartoon(update, context):
	path=saveImage(update, context)
	update.message.reply_text("got it")
	Lpath=path+"_cartoon.jpg"
	update.message.reply_text("cartoonify your image!")
	#_, arg1, arg2 = context.chat_data['rescale'].split(' ')
	run(['gmic', path, 'cartoon', '4,25,10,0.1,1.2,16', 'output', Lpath])
	try:
		with open(Lpath, 'rb') as f:
			update.message.reply_document(f)
		update.message.reply_text("here is the cartoonifyed image!")
	except Exception as e:
		print(e)
		update.message.reply_text("image could not be cartoonifyed")
	return ConversationHandler.END
######################################
######################################
def stack_command(update, context):
	args=update.message.text.split(' ')[-1].lower()
	if args=="ecc":
		context.chat_data['alg'] = "ecc"
		update.message.reply_text("using ECC method expect longer waiting time")
	elif args=="orb":
		context.chat_data['alg'] = "orb"
		update.message.reply_text("using orb method expect very fast results with less accuracy")
	elif args=="static":
		context.chat_data['alg'] = "static"
		update.message.reply_text("using static method, this gives the fastest results but uses no alignment whatsoever")
	else:
		context.chat_data['alg'] = "comb"
	update.message.reply_text('start sending images and send \'end\' to stop and process')
	return 'getimg'

def process_stack(update, context):
	update.message.reply_text("now wait")
	outName=str(update.update_id)
	img=stackImages(context.chat_data['pano'], update, mode=context.chat_data['alg'])
	imwrite(outName+".jpg", cv2.resize(img, (0,0), fx=0.5, fy=0.5))
	imwrite(outName+".png", img)
	try:
		with open(outName+".jpg", 'rb') as f:
			try: update.message.reply_photo(f)
			except Exception as e:
				print(e)
				update.message.reply_text("couldn't send as photo")
		with open(outName+".png", 'rb') as f:
			update.message.reply_document(f)
		update.message.reply_text("there you go!")
	except Exception as e:
		print(e)
		update.message.reply_text("couldn't stack the images")
	context.chat_data['pano']=[]
	return ConversationHandler.END

def saveFace_command(update, context):
	if update.message.reply_to_message is None:
		update.message.reply_text("send me an image of a single person and then his name")
		return 'getimg'
	else:
		update.message.reply_text("now send me the name of that person")
		if update.message.reply_to_message.document is None:
			file=update.message.reply_to_message.photo[-1].get_file()
		else:
			file=update.message.reply_to_message.document.get_file()
		path="img/" + str(file.file_unique_id)
		file.download(custom_path=path)
		if 'faces' not in context.chat_data: context.chat_data['faces']=[]
		context.chat_data['faces'].append(["unknown", saveFace(path)])
		return "getname"

def process_saveFace(update, context):
	path=saveImage(update, context)
	update.message.reply_text("got it")
	if 'faces' not in context.chat_data: context.chat_data['faces']=[]
	context.chat_data['faces'].append(["unknown", saveFace(path)])
	return "getname"

def saveFace_name(update, context):
	context.chat_data['faces'][-1][0]=update.message.text
	update.message.reply_text("the face was saved succesfully!")
	return ConversationHandler.END

def main():
	"""Start the bot."""
	run(["mkdir", "img"])
	pp = PicklePersistence(filename='imageGroup')
	with open("tk", 'r') as tk:
		updater = Updater(tk.read()[:-1], persistence=pp, use_context=True)
	# Get the dispatcher to register handlers
	dp = updater.dispatcher

	# on different commands - answer in Telegram
	dp.add_handler(CommandHandler("start", start))
	dp.add_handler(CommandHandler("help", help_command))
	dp.add_handler(CommandHandler("get", get_command))
	dp.add_handler(CommandHandler("shutdown", shutdown_command))

	conv_handler = ConversationHandler(
		entry_points=[CommandHandler("pano", pano_command)],
		states={
			'getimg': [MessageHandler(Filters.document.image | Filters.photo & ~Filters.command, pano_image_recieve), MessageHandler(Filters.text & ~Filters.command, process_pano)]
		},
		fallbacks=[CommandHandler("cancel",cancel_command)],
		allow_reentry=True
	)
	dp.add_handler(conv_handler)
	conv_handler = ConversationHandler(
		entry_points=[CommandHandler("stack", stack_command)],
		states={
			'getimg': [MessageHandler(Filters.document.image | Filters.photo & ~Filters.command, pano_image_recieve), MessageHandler(Filters.text & ~Filters.command, process_stack)]
		},
		fallbacks=[],
		allow_reentry=True
	)
	dp.add_handler(conv_handler)
	conv_handler = ConversationHandler(
		entry_points=[CommandHandler("cartoon", cartoon_command)],
		states={
			'getimg': [MessageHandler(Filters.document.image | Filters.photo & ~Filters.command, process_cartoon)]
		},
		fallbacks=[CommandHandler("cancel",cancel_command)],
		allow_reentry=True
	)
	dp.add_handler(conv_handler)
	conv_handler = ConversationHandler(
		entry_points=[CommandHandler("rescale", rescale_command)],
		states={
			'getimg': [MessageHandler(Filters.document.image | Filters.photo & ~Filters.command, process_rescale)]
		},
		fallbacks=[CommandHandler("cancel",cancel_command)],
		allow_reentry=True
	)
	dp.add_handler(conv_handler)
	conv_handler = ConversationHandler(
		entry_points=[CommandHandler("saveface", saveFace_command)],
		states={
			'getimg': [MessageHandler(Filters.document.image | Filters.photo & ~Filters.command, process_saveFace)],
			'getname': [MessageHandler(Filters.text & ~Filters.command, saveFace_name)]
		},
		fallbacks=[CommandHandler("cancel",cancel_command)],
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

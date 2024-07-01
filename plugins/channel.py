from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from info import CHANNELS, MOVIE_UPDATE_CHANNEL, ADMINS
from database.ia_filterdb import save_file, unpack_new_file_id
from utils import get_poster, temp
import re
from Script import script

processed_movies = set()

media_filter = filters.document | filters.video

@Client.on_message(filters.chat(CHANNELS) & media_filter)
async def media(bot, message):
    media = getattr(message, message.media.value, None)
    if media.mime_type in ['video/mp4', 'video/x-matroska']: 
        media.file_type = message.media.value
        media.caption = message.caption
        success_sts = await save_file(media)
        if success_sts == 'suc':
            file_id, file_ref = unpack_new_file_id(media.file_id)
            await send_movie_updates(bot, file_name=media.file_name, file_id=file_id)

def name_format(file_name: str):
    file_name = file_name.lower()
    file_name = re.sub(r'http\S+', '', re.sub(r'@\w+|#\w+', '', file_name).replace('_', ' ').replace('[', '').replace(']', '')).strip()
    file_name = re.split(r's\d+|season\s*\d+|chapter\s*\d+', file_name, flags=re.IGNORECASE)[0]
    file_name = file_name.strip()
    words = file_name.split()[:4]
    imdb_file_name = ' '.join(words)
    return imdb_file_name

app = Client("RFADVANCEBOT")

async def get_imdb(file_name):
    imdb_file_name = name_format(file_name)
    imdb = await get_poster(imdb_file_name)
    if imdb:
        caption = script.MOVIES_UPDATE_TXT.format(
            title=imdb.get('title'),
            rating=imdb.get('rating'),
            genre=imdb.get('genre'),
            description=imdb.get('plot'),
        )
        return imdb.get('title'), imdb.get('poster'), caption
    return None, None, None
    
async def send_movie_updates(client, file_name, file_id):
    imdb_title, poster_url, caption = await get_imdb(file_name)
    if imdb_title in processed_movies:
        return
    processed_movies.add(imdb_title)
    if not poster_url or not caption:
        return
    # Replace spaces in the movie title with underscores for URL encoding
    encoded_movie_title = imdb_title.replace(" ", "_")
    # Update the deep link URL to include the search query parameter
    deep_link_url = f'https://t.me/{temp.U_NAME}?start=search_{encoded_movie_title}'
    btn = [
        [InlineKeyboardButton('Get File', url=deep_link_url)]
    ]
    reply_markup = InlineKeyboardMarkup(btn)
    await client.send_photo(chat_id=MOVIE_UPDATE_CHANNEL, photo=poster_url, caption=caption, reply_markup=reply_markup)

# Define a handler for /start command
@app.on_message(filters.command("start"))
async def start_command(client, message):
    # Extract the parameter from the /start command
    query = message.text.split(' ')[1] if len(message.text.split(' ')) > 1 else ''
    if query.startswith('search_'):
        search_query = query.split('search_')[1].replace('_', ' ')
        # Call your existing search logic function
        await auto_filter(client, message, spoll=False, pm_mode=True)

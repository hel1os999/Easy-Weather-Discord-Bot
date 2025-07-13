import discord  # Import the Discord.py library for interacting with the Discord API
from discord.ext import commands  # Import commands module for creating bot commands
import aiohttp  # Import aiohttp for making asynchronous HTTP requests
import re  # Import re for regular expression operations
import logging  # Import logging for logging bot activity
import os  # Import os for accessing environment variables
from dotenv import load_dotenv  # Import load_dotenv to load environment variables from a .env.example file

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')  # Configure logging with INFO level and a custom format
logger = logging.getLogger(__name__)  # Create a logger instance for the current module

# Load environment variables from .env.example
load_dotenv()  # Load variables from a .env.example file into the environment

# Retrieve keys from environment variables
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")  # Get the Discord bot token from environment variables
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")  # Get the WeatherAPI key from environment variables

# Check if keys are loaded
if not DISCORD_BOT_TOKEN or not WEATHER_API_KEY:  # Verify that both keys are present
    logger.error("DISCORD_BOT_TOKEN or WEATHER_API_KEY not found in .env.example")  # Log an error if keys are missing
    exit(1)  # Exit the program with an error code

# Set up intents
intents = discord.Intents.default()  # Create a default intents object
intents.message_content = True  # Enable access to message content for the bot

# Initialize bot with command prefix
bot = commands.Bot(command_prefix='!', intents=intents)  # Create a bot instance with '!' as the command prefix and specified intents

def clean_city_name(city_name):  # Define a function to clean and normalize city names
    """Cleans the city name by removing invalid characters and normalizing it."""
    city_name = re.sub(r"[^a-zA-Zа-яА-ЯёЁ\s-]", "", city_name).strip()  # Remove invalid characters and trim whitespace
    return ' '.join(city_name.split())  # Normalize spaces by joining words with a single space

async def get_weather(city):  # Define an async function to fetch weather data for a given city
    """Fetches weather data from WeatherAPI."""
    url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}&lang=en"  # Construct the API request URL
    logger.debug(f"Request URL: {url}")  # Log the constructed URL for debugging

    async with aiohttp.ClientSession() as session:  # Create an aiohttp client session
        try:
            async with session.get(url, timeout=10) as response:  # Make an HTTP GET request with a 10-second timeout
                logger.debug(f"Status Code: {response.status}")  # Log the HTTP response status code
                if response.status != 200:  # Check if the response status is not OK
                    return None, f"Request error: HTTP {response.status}"  # Return None and an error message

                data = await response.json()  # Parse the JSON response
                logger.debug(f"Response Data: {data}")  # Log the response data for debugging

                if "error" in data:  # Check if the response contains an error
                    error_msg = data['error']['message']  # Extract the error message
                    if "No matching location found" in error_msg:  # Handle specific error for city not found
                        return None, "City not found. Please check the spelling."
                    return None, f"API error: {error_msg}"  # Return other API errors

                try:
                    location = data["location"]["name"]  # Extract city name
                    country = data["location"]["country"]  # Extract country name
                    temp = data["current"]["temp_c"]  # Extract temperature in Celsius
                    condition = data["current"]["condition"]["text"]  # Extract weather condition description
                    icon = "http:" + data["current"]["condition"]["icon"]  # Construct full URL for weather icon
                    return {  # Return a dictionary with weather data
                        "location": location,
                        "country": country,
                        "temp": temp,
                        "condition": condition,
                        "icon": icon
                    }, None  # No error
                except KeyError:  # Handle missing keys in the API response
                    return None, "Error parsing API data."
        except aiohttp.ClientError as e:  # Handle network-related errors
            logger.error(f"Network error: {e}")  # Log the error
            return None, "Network error. Please try again later."  # Return error message

@bot.event
async def on_ready():  # Define an event handler for when the bot is ready
    logger.info(f"✅ Bot started as {bot.user}")  # Log that the bot has successfully started

@bot.command(name="weather")  # Define a bot command named 'weather'
async def weather_command(ctx, *, city):  # Define the command handler with a city argument
    """Command to get weather for a specified city."""
    city = clean_city_name(city)  # Clean the provided city name

    if not city:  # Check if the city name is empty after cleaning
        await ctx.send("❌ Please enter a city name, e.g., !weather London")  # Send an error message
        return

    weather_data, error = await get_weather(city)  # Fetch weather data for the city

    if error:  # Check if there was an error
        await ctx.send(error)  # Send the error message to the Discord channel
        return

    embed = discord.Embed(  # Create an embedded message for the weather data
        title=f"Weather in {weather_data['location']}, {weather_data['country']}",  # Set the title with location
        description=f"{weather_data['condition']}, {weather_data['temp']}°C",  # Set the description with condition and temperature
        color=0x87CEEB  # Set embed color to a sky blue
    )
    embed.set_thumbnail(url=weather_data['icon'])  # Set the weather icon as the thumbnail
    await ctx.send(embed=embed)  # Send the embedded message to the Discord channel

# Start the bot
bot.run(DISCORD_BOT_TOKEN)  # Run the bot with the provided Discord token
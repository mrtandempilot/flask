import os
from datetime import datetime
from flask import Flask, render_template, request, send_from_directory, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from newsapi import NewsApiClient
from dotenv import load_dotenv
import requests
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

# Configure upload folder
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Database Config
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'photos.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize NewsAPI
NEWS_API_KEY = os.getenv('NEWS_API_KEY')

# Initialize database
db = SQLAlchemy(app)

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class NewsItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=False)
    url = db.Column(db.String(500), nullable=False)
    image_url = db.Column(db.String(500))
    published_at = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<NewsItem {self.title}>'

class SportsNews(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=False)
    url = db.Column(db.String(500), nullable=False)
    image_url = db.Column(db.String(500))
    published_at = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<SportsNews {self.title}>'

class WeatherForecast(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    feels_like = db.Column(db.Float, nullable=False)
    temp_min = db.Column(db.Float, nullable=False)
    temp_max = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Integer, nullable=False)
    wind_speed = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(10), nullable=False)
    fetch_time = db.Column(db.DateTime, default=datetime.utcnow)

class FethiyeWeatherForecast(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    feels_like = db.Column(db.Float, nullable=False)
    temp_min = db.Column(db.Float, nullable=False)
    temp_max = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Integer, nullable=False)
    wind_speed = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(10), nullable=False)

# Create all database tables
with app.app_context():
    db.drop_all()  # Drop all existing tables
    db.create_all()  # Create all tables with new schema

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def fetch_and_store_news():
    try:
        newsapi = NewsApiClient(api_key=NEWS_API_KEY)
        
        # Clear existing news
        NewsItem.query.delete()
        
        # Get weather-related news
        weather_news = newsapi.get_everything(
            q='weather OR climate',
            language='en',
            sort_by='publishedAt',
            page_size=10
        )
        
        # Store new weather articles
        for article in weather_news['articles']:
            if article['title'] and article['description'] and article['url']:
                news_item = NewsItem(
                    title=article['title'],
                    description=article['description'],
                    url=article['url'],
                    image_url=article.get('urlToImage'),
                    published_at=datetime.strptime(article['publishedAt'], '%Y-%m-%dT%H:%M:%SZ')
                )
                db.session.add(news_item)
        
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error fetching news: {str(e)}")
        return False

def fetch_sports_news():
    try:
        newsapi = NewsApiClient(api_key=NEWS_API_KEY)
        
        # Clear existing sports news
        SportsNews.query.delete()
        
        # Get sports news
        sports_news = newsapi.get_everything(
            q='sports',
            language='en',
            sort_by='publishedAt',
            page_size=20
        )
        
        # Store new sports articles
        for article in sports_news['articles']:
            if article['title'] and article['description'] and article['url']:
                news_item = SportsNews(
                    title=article['title'],
                    description=article['description'],
                    url=article['url'],
                    image_url=article.get('urlToImage'),
                    published_at=datetime.strptime(article['publishedAt'], '%Y-%m-%dT%H:%M:%SZ')
                )
                db.session.add(news_item)
        
        db.session.commit()
        print("Sports news fetched and stored successfully")
        return True
    except Exception as e:
        print(f"Error fetching sports news: {str(e)}")
        return False

def fetch_weather_forecast():
    try:
        api_key = os.getenv('OPENWEATHER_API_KEY')
        url = f'https://api.openweathermap.org/data/2.5/forecast?q=Istanbul,TR&appid={api_key}&units=metric'
        
        response = requests.get(url)
        data = response.json()
        
        # Clear existing forecasts
        WeatherForecast.query.delete()
        
        # Get one forecast per day (every 24 hours)
        processed_dates = set()
        for item in data['list']:
            forecast_date = datetime.fromtimestamp(item['dt'])
            date_key = forecast_date.date()
            
            if date_key not in processed_dates:
                processed_dates.add(date_key)
                
                forecast = WeatherForecast(
                    date=forecast_date,
                    temperature=item['main']['temp'],
                    feels_like=item['main']['feels_like'],
                    temp_min=item['main']['temp_min'],
                    temp_max=item['main']['temp_max'],
                    humidity=item['main']['humidity'],
                    description=item['weather'][0]['description'],
                    icon=item['weather'][0]['icon'],
                    wind_speed=item['wind']['speed']
                )
                db.session.add(forecast)
                
                # Stop after 5 days
                if len(processed_dates) >= 5:
                    break
        
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error fetching weather forecast: {str(e)}")
        return False

def fetch_fethiye_weather():
    api_key = os.getenv('OPENWEATHER_API_KEY')
    url = f'https://api.openweathermap.org/data/2.5/forecast?q=Fethiye,TR&appid={api_key}&units=metric'
    
    try:
        response = requests.get(url)
        data = response.json()
        
        # Clear existing forecasts
        FethiyeWeatherForecast.query.delete()
        
        for item in data['list']:
            forecast = FethiyeWeatherForecast(
                date=datetime.fromtimestamp(item['dt']),
                temperature=item['main']['temp'],
                feels_like=item['main']['feels_like'],
                temp_min=item['main']['temp_min'],
                temp_max=item['main']['temp_max'],
                humidity=item['main']['humidity'],
                wind_speed=item['wind']['speed'],
                description=item['weather'][0]['description'],
                icon=item['weather'][0]['icon']
            )
            db.session.add(forecast)
        
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return False

def get_clothing_recommendation(temp, weather_condition, wind_speed):
    recommendations = {
        'top': [],
        'bottom': [],
        'footwear': [],
        'accessories': []
    }
    
    # Temperature based recommendations
    if temp < 10:
        recommendations['top'].extend(['Heavy winter coat', 'Thick sweater', 'Thermal undershirt'])
        recommendations['bottom'].extend(['Warm pants', 'Thermal leggings'])
        recommendations['footwear'].append('Winter boots')
        recommendations['accessories'].extend(['Warm hat', 'Scarf', 'Gloves'])
    elif temp < 15:
        recommendations['top'].extend(['Light jacket', 'Long sleeve shirt', 'Light sweater'])
        recommendations['bottom'].append('Long pants')
        recommendations['footwear'].append('Closed shoes')
        recommendations['accessories'].append('Light scarf')
    elif temp < 20:
        recommendations['top'].extend(['Light jacket or cardigan', 'Long sleeve shirt'])
        recommendations['bottom'].append('Long pants or jeans')
        recommendations['footwear'].append('Sneakers or loafers')
    elif temp < 25:
        recommendations['top'].extend(['T-shirt', 'Light shirt'])
        recommendations['bottom'].append('Light pants or jeans')
        recommendations['footwear'].extend(['Sneakers', 'Light shoes'])
        recommendations['accessories'].append('Sunglasses')
    else:
        recommendations['top'].extend(['Light T-shirt', 'Tank top'])
        recommendations['bottom'].extend(['Shorts', 'Light pants'])
        recommendations['footwear'].extend(['Sandals', 'Light shoes'])
        recommendations['accessories'].extend(['Sunglasses', 'Sun hat'])
    
    # Weather condition based additions
    if 'rain' in weather_condition.lower():
        recommendations['accessories'].append('Umbrella')
        recommendations['footwear'] = ['Waterproof shoes']
        if temp < 20:
            recommendations['top'].append('Rain jacket')
    
    if 'cloud' in weather_condition.lower() and temp > 20:
        recommendations['top'].append('Light jacket')
    
    if wind_speed > 20:  # If wind speed is greater than 20 km/h
        recommendations['accessories'].append('Windbreaker')
        if temp > 20:
            recommendations['accessories'].append('Hat to protect from wind')
    
    return recommendations

@app.route('/')
def home():
    try:
        # Fetch fresh data
        fetch_and_store_news()
        fetch_sports_news()
        fetch_weather_forecast()
        fetch_fethiye_weather()
        
        # Get data for template
        photos = Photo.query.order_by(Photo.upload_date.desc()).all()
        weather_news = NewsItem.query.order_by(NewsItem.published_at.desc()).limit(3).all()
        sports_news = SportsNews.query.order_by(SportsNews.published_at.desc()).limit(3).all()
        
        return render_template('home.html', 
                             photos=photos,
                             weather_news=weather_news,
                             sports_news=sports_news,
                             WeatherForecast=WeatherForecast,
                             FethiyeWeatherForecast=FethiyeWeatherForecast)
    except Exception as e:
        print(f"Error in home route: {str(e)}")
        return render_template('home.html', 
                             photos=[],
                             weather_news=[],
                             sports_news=[],
                             WeatherForecast=WeatherForecast,
                             FethiyeWeatherForecast=FethiyeWeatherForecast)

@app.route('/news')
def news():
    # Fetch fresh weather news
    fetch_and_store_news()
    news_items = NewsItem.query.order_by(NewsItem.published_at.desc()).all()
    return render_template('news.html', news_items=news_items)

@app.route('/sports')
def sports():
    try:
        # Fetch fresh sports news
        fetch_sports_news()
        
        # Get all sports news ordered by published date
        sports_news = SportsNews.query.order_by(SportsNews.published_at.desc()).all()
        
        # Debug print
        print(f"Number of sports news articles: {len(sports_news)}")
        
        return render_template('sports.html', sports_news=sports_news)
    except Exception as e:
        print(f"Error in sports route: {str(e)}")
        return render_template('sports.html', sports_news=[])

@app.route('/weather')
def weather():
    # Fetch fresh Istanbul weather
    fetch_weather_forecast()
    forecasts = WeatherForecast.query.order_by(WeatherForecast.date).all()
    return render_template('weather.html', forecasts=forecasts)

@app.route('/fethiye-weather')
def fethiye_weather():
    # Fetch fresh Fethiye weather
    fetch_fethiye_weather()
    forecasts = FethiyeWeatherForecast.query.order_by(FethiyeWeatherForecast.date).all()
    return render_template('fethiye_weather.html', forecasts=forecasts)

@app.route('/what-to-wear')
def what_to_wear():
    try:
        # Fetch fresh Fethiye weather
        fetch_fethiye_weather()
        
        # Get the latest weather data
        current_weather = FethiyeWeatherForecast.query.order_by(FethiyeWeatherForecast.date).first()
        
        if current_weather:
            # Get clothing recommendations
            recommendations = get_clothing_recommendation(
                current_weather.temperature,
                current_weather.description,
                current_weather.wind_speed
            )
            
            return render_template(
                'what_to_wear.html',
                weather=current_weather,
                recommendations=recommendations
            )
        else:
            flash('Unable to fetch weather data. Please try again later.')
            return render_template('what_to_wear.html', weather=None, recommendations=None)
            
    except Exception as e:
        print(f"Error in what_to_wear route: {str(e)}")
        flash('An error occurred. Please try again later.')
        return render_template('what_to_wear.html', weather=None, recommendations=None)

@app.route('/upload_file', methods=['POST'])
def upload_file():
    if 'photo' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['photo']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        # Generate secure filename
        filename = secure_filename(file.filename)
        # Ensure filename is unique
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
            filename = f"{base}_{counter}{ext}"
            counter += 1
            
        # Save file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Create database entry
        photo = Photo(filename=filename, upload_date=datetime.utcnow())
        db.session.add(photo)
        db.session.commit()
        
        flash('Photo uploaded successfully!')
        return redirect(url_for('home'))
    
    flash('Invalid file type')
    return redirect(url_for('home'))

@app.route('/download_file/<filename>')
def download_file(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except Exception as e:
        flash('Error downloading file')
        return redirect(url_for('home'))

@app.route('/gallery')
def gallery():
    photos = Photo.query.order_by(Photo.upload_date.desc()).all()
    return render_template('gallery.html', photos=photos)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

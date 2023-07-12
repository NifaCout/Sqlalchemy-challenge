# Import the dependencies.
import numpy as np
import sqlalchemy
import datetime as dt
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import create_engine, text, inspect, func
from flask import Flask, jsonify


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
#Base.prepare(engine, reflect=True)
Base.prepare(autoload_with=engine)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station


# Create our session (link) from Python to the DB
#session = Session(engine)

#################################################
# Flask Setup
#################################################
# Create an instance of Flask
app = Flask(__name__)


#################################################
# Flask Routes
#################################################
 
#Define the home route
@app.route('/')
def home():
    return (
        f"Welcome to Weather Analysis!<br/><br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start_date<br/>"
        f"/api/v1.0/start_date/end_date"
    )

# precipitation route
@app.route('/api/v1.0/precipitation')
def precipitation():
    session = Session(engine)

# Calculate the date one year from the last date in the data set
    recent_data = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    last_date = dt.datetime.strptime(recent_data[0], '%Y-%m-%d')
    year_ago = last_date - dt.timedelta(days=365)

    # query to retrieve precipitation data for the 12 months
    precipitation = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= year_ago).all()

    session.close()

    # Create a dictionary of date and precipitation values
    precipitation_data = {date: prcp for date, prcp in precipitation}

    # Return the JSONified precipitation data
    return jsonify(precipitation_data)

# stations route
@app.route('/api/v1.0/stations')
def stations():
    session = Session(engine)

    # Query all stations
    total_stations = session.query(Station.station).all()

    session.close()

    # Convert the data to a list
    stations_list = [station[0] for station in total_stations]

    # Return the JSONified data
    return jsonify(stations_list)

# temperature observations route
@app.route('/api/v1.0/tobs')
def tobs():
    session = Session(engine)

    # Calculate the date one year from the last date in the data set
    recent_data = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    last_date = dt.datetime.strptime(recent_data[0], '%Y-%m-%d')
    year_ago = last_date - dt.timedelta(days=365)

    # Query the most active station
    active_stations = session.query(Measurement.station, func.count(Measurement.station)).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).all()
    most_active_station = active_stations[0][0]

    # Query temperature observations for the most active station for the previous year
    temp_data = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.date >= year_ago).\
        filter(Measurement.station == most_active_station).all()

    session.close()

    # List of temperature observations
    temp_list = [temp[1] for temp in temp_data]

    # Return the JSONified data
    return jsonify(temp_list)


@app.route('/api/v1.0/<start>')
def temperature_stats_start(start):
    session = Session(engine)

    # Query the most active station
    active_stations = session.query(Measurement.station, func.count(Measurement.station)).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).all()
    most_active_station = active_stations[0][0]

    # Query the temperature statistics for dates greater than or equal to the start date
    temperature_stats = session.query(func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs)).\
        filter(Measurement.date >= start).\
        filter(Measurement.station == most_active_station).all()

    session.close()

    # Extract the temperature statistics from the query results
    lowest_temp = temperature_stats[0][0]
    highest_temp = temperature_stats[0][1]
    avg_temp = temperature_stats[0][2]

    # Create a dictionary with temperature statistics
    temperature_data = {
        'TMIN': lowest_temp,
        'TAVG': avg_temp,
        'TMAX': highest_temp
    }

    # Return the JSONified temperature data
    return jsonify(temperature_data)

# start/end date route
@app.route('/api/v1.0/<start>/<end>')
def temperature_stats_start_end(start, end):
    session = Session(engine)

    # Query temperature statistics for the specified date range
    temperature_stats = session.query(func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs)).\
        filter(Measurement.date >= start).\
        filter(Measurement.date <= end).all()

    session.close()

    # Check if any results are returned
    if temperature_stats:
        # Extract the temperature statistics from the first row of the query results
        lowest_temp = temperature_stats[0][0]
        highest_temp = temperature_stats[0][1]
        avg_temp = temperature_stats[0][2]

        # Create a dictionary with temperature statistics
        temperature_data = {
            'TMIN': lowest_temp,
            'TAVG': avg_temp,
            'TMAX': highest_temp
        }
        # Return the JSONified temperature data
        return jsonify(temperature_data)
    else:
        # Return a message or appropriate response when no results are found
        return jsonify({'message': 'No temperature data available for the specified date range.'})

# Run the application
if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, render_template, request
from life_expectancy_predictor import Life_Expectancy_Predictor_Engine

app = Flask(__name__)

# Create the predictor object when the app starts.
# The model will be loaded and trained then kept in memory and used for all predictions.
print("Flask app starting... Initializing model.")
try:
    predictor = Life_Expectancy_Predictor_Engine()       # Initialize the predictor engine
    dropdown_options = predictor.get_dropdown_options()  # Get dropdown options for the form from engine
    print("Flask app is trained and ready to serve predictions.")
    
except Exception as e:
    print(f"FATAL ERROR: Could not initialize model. {e}")
    predictor = None
    dropdown_options = { 'states': [], 'years': [], 'races': [], 'sexes': [], 'state_county_map': {}}

# --- Flask Routes ---

@app.route('/', methods=['GET', 'POST'])
def home():
    #Main route that handles both displaying the form (GET) and processing the prediction (POST).
    if predictor is None:     # If model failed to load, show an error page.
        return "Error: Model could not be loaded. Please check server logs.", 500
        
    prediction_text = None

    if request.method == 'POST':
        try:
            # --- Get data from the form ---
            state = request.form.get('state')
            county = request.form.get('county')
            year = int(request.form.get('year')) # Year needs to be an integer
            race = request.form.get('race')
            sex = request.form.get('sex')

            # --- Make the prediction ---
            prediction = predictor.make_prediction(state=state,county=county,year=year,race=race, sex=sex)
            prediction_text = f"{prediction:.2f} years"

        except Exception as e:
            print(f"Error during prediction: {e}")
            prediction_text= f"Error: Could not make prediction. {e}"

    # Render page for both GET and POST requests.
    # POST: re-renders page with prediction_result.
    # GET: as prediction_result is None, the 'if' block in HTML is false.
    return render_template(
        'index.html',prediction=prediction_text, states=dropdown_options['states'], 
        years=dropdown_options['years'], races=dropdown_options['races'], 
        sexes=dropdown_options['sexes'], state_county_map=dropdown_options['state_county_map'] )

if __name__ == '__main__':
    app.run(debug=False)
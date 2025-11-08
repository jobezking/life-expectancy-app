import pandas as pd
import sqlite3
import numpy as np
import warnings

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, BayesianRidge
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.experimental import enable_iterative_imputer  # required
from sklearn.impute import SimpleImputer, IterativeImputer
from sklearn.ensemble import StackingRegressor

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)


class Life_Expectancy_Predictor_Engine:
    #This class loads data and trains the model ONCE upon initialization.
    #It then provides a method to make fast predictions and a helper to get data for web form dropdowns.

    def __init__(self):
        # Initializes predictor engine. This constructor:
        # 1. Defines the preprocessors.
        # 2. Loads data from the specified SQLite database.
        # 3. Creates the master dataset.
        # 4. Trains the final StackingRegressor model.
  
        print("Initializing Engine: Loading data...")
        # imputers and encoders
        self.iter_imputer = IterativeImputer(estimator=BayesianRidge(), random_state=42) # iterative imputer for numerical features
        self.simple_imputer = SimpleImputer(strategy='most_frequent')                    # simple imputer for categorical features
        self.encoder = OneHotEncoder(handle_unknown='ignore')                            # one-hot encoder for categorical features

        # database file
        self.db_file = "life_expectancy_tables.db"          # contained prepared data tables from each source CSV file

        # define class variables
        self.full_dataset = None            # Complete dataset made by combining all tables 
        self.ALL_FEATURES = None            # List of all feature column names
        self.STACKING_MODEL = None          # The final stacking model
        self.X_train = None                 # Training features
        self.y_train = None                 # Training target variable

        # --- Run all setup methods ---
        try:
            self._load_data_to_dataset()    # load prepared data
            self._train_test_split()        # split data into train/test
            self._build_pipelines()          # build pipelines for individual models
            self._build_stacking_model()    # build ensemble stacking model from individual models
            
            print("Training the Stacking Ensemble Model...")
            self._train_stacking_model()    # train the final stacking model
            print("Engine is trained and ready.")

        except sqlite3.OperationalError:
            print(f"CRITICAL ERROR: Database file '{self.db_file}' not found.")
            print("Please ensure the database is in the same directory.")
            raise
        except Exception as e:
            print(f"An error occurred during initialization: {e}")
            raise
    
    def _load_data_to_dataset(self): # Load tables from SQLite database into DataFrames. 
        #data was previously prepared when read from original CSV files and loaded into SQlite DB. Can simply be used.
        #ssa_life_expectancy_sex_year   #SSA_Life_Expectancy_by_sex_1940_2001.csv and SSA_Life_Expectancy_by_sex_2002_2080.csv: SSA.gov
        #life_expectancy_sex_state      #U.S._State_Life_Expectancy_by_Sex__2020.csv: Kaggle.com
        #life_expectancy_state_county   #U.S._Life_Expectancy_at_Birth_by_State_and_Census_Tract_-_2010-2015.csv: CDC.gov
        #life_expectancy_race_sex       #NCHS_-_Death_rates_and_life_expectancy_at_birth.csv: Kaggle.com
        #life_expectancy_race_sex_year  #133_life_expectancy_data.csv: data.gov

        conn = sqlite3.connect(self.db_file)        #connect to SQLite database
        datasets = []                               #list for dataframes for all model tables
        datasets.append(pd.read_sql("SELECT * FROM ssa_life_expectancy_sex_year", conn))
        datasets.append(pd.read_sql("SELECT * FROM life_expectancy_sex_state", conn))
        datasets.append(pd.read_sql("SELECT * FROM life_expectancy_state_county", conn))
        datasets.append(pd.read_sql("SELECT * FROM life_expectancy_race_sex", conn))
        datasets.append(pd.read_sql("SELECT * FROM life_expectancy_race_sex_year", conn))
        conn.close()

        self.full_dataset = pd.concat(datasets,ignore_index=True, sort=False)   #create master dataset by combining all model tables
        self.full_dataset = self.full_dataset.dropna(subset=['LifeExpectancy']) #drop rows with missing target variable

    def _train_test_split(self):        #   Split dataset into train/test sets.
        X = self.full_dataset.drop('LifeExpectancy', axis=1)       #obtain features
        y = self.full_dataset['LifeExpectancy']                    #obtain target variable
        self.ALL_FEATURES = X.columns.tolist()                      #store feature names
        # We'll use the full dataset for training the final production model
        self.X_train = X
        self.y_train = y

    def _build_sex_year_pipeline(self):         # Builds the pipeline sex_year model.
        transformer = ColumnTransformer(transformers=[
            ('year', Pipeline([
                ('imputer', self.iter_imputer),
                ('scaler', StandardScaler())
            ]), ['Year']),
            ('sex', Pipeline([
                ('imputer', self.simple_imputer),
                ('encoder', self.encoder)
            ]), ['Sex'])
        ], remainder='drop')

        return Pipeline(steps=[('transformer', transformer),('model', LinearRegression())])

    def _build_sex_state_pipeline(self):        # Builds the pipeline for sex_state model.
        transformer = ColumnTransformer(transformers=[
            ('state', Pipeline([
                ('imputer', self.simple_imputer),
                ('encoder', self.encoder)
            ]), ['State']),
            ('sex', Pipeline([
                ('imputer', self.simple_imputer),
                ('encoder', self.encoder)
            ]), ['Sex'])
        ], remainder='drop')

        return Pipeline(steps=[('transformer', transformer), ('model', LinearRegression())])

    def _build_state_county_pipeline(self):         # Builds the pipeline for state_county model.
        transformer = ColumnTransformer(transformers=[
            ('state', Pipeline([
                ('imputer', self.simple_imputer),
                ('encoder', self.encoder)
            ]), ['State']),
            ('county', Pipeline([
                ('imputer', self.simple_imputer),
                ('encoder', self.encoder)
            ]), ['County'])
        ], remainder='drop')

        return Pipeline(steps=[('transformer', transformer), ('model', LinearRegression())])

    def _build_race_sex_pipeline(self):        #  Builds the pipeline for race_sex model.
        transformer = ColumnTransformer(transformers=[
            ('year', Pipeline([
                ('imputer', self.iter_imputer),
                ('scaler', StandardScaler())
            ]), ['Year']),
            ('sex', Pipeline([
                ('imputer', self.simple_imputer),
                ('encoder', self.encoder)
            ]), ['Sex']),
            ('race', Pipeline([
                ('imputer', self.simple_imputer),
                ('encoder', self.encoder)
            ]), ['Race']),
            ('deathrate', Pipeline([
                ('imputer', self.simple_imputer),
                ('encoder', self.encoder)
            ]), ['AgeAdjustedDeathRate'])
        ], remainder='drop')

        return Pipeline(steps=[('transformer', transformer), ('model', LinearRegression())])

    def _build_race_sex_year_pipeline(self):    #  Builds the pipeline for race_sex_year model.
        transformer = ColumnTransformer(transformers=[
            ('year', Pipeline([
                ('imputer', self.iter_imputer),
                ('scaler', StandardScaler())
            ]), ['Year']),
            ('sex', Pipeline([
                ('imputer', self.simple_imputer),
                ('encoder', self.encoder)
            ]), ['Sex']),
            ('race', Pipeline([
                ('imputer', self.simple_imputer),
                ('encoder', self.encoder)
            ]), ['Race'])
        ], remainder='drop')

        return Pipeline(steps=[('transformer', transformer), ('model', LinearRegression())])
    
    def _build_pipelines(self):          #Builds all individual pipelines. 
        self.sex_year_pipeline = self._build_sex_year_pipeline()
        self.sex_state_pipeline = self._build_sex_state_pipeline()
        self.state_county_pipeline = self._build_state_county_pipeline()
        self.race_sex_pipeline = self._build_race_sex_pipeline()
        self.race_sex_year_pipeline = self._build_race_sex_year_pipeline()
            
    def _build_stacking_model(self): #   Builds the StackingRegressor using the individual pipelines and models.
        estimators = [
            ('sex_year_model', self.sex_year_pipeline),
            ('sex_state_model', self.sex_state_pipeline),
            ('state_county_model', self.state_county_pipeline),
            ('race_sex_model', self.race_sex_pipeline),
            ('race_sex_year_model', self.race_sex_year_pipeline)
        ]
        self.STACKING_MODEL = StackingRegressor(estimators=estimators,final_estimator=LinearRegression(),
                                                cv=5,passthrough=False)
        
   

    def _train_stacking_model(self):    #Trains the final stacking model on the full dataset. 
        self.STACKING_MODEL.fit(self.X_train, self.y_train)

    def get_dropdown_options(self): #   Extracts unique, sorted lists for the form dropdowns and a map of states to their counties.
        if self.full_dataset is None:
            return {}

        try:        # Get flat lists
            states_list = sorted(self.full_dataset['State'].dropna().unique())
            years_list0 = sorted(self.full_dataset['Year'].dropna().unique())
            years_list = [int(year) for year in years_list0] # Convert floats to ints for dropdown
            races_list = sorted(self.full_dataset['Race'].dropna().unique())
            sexes_list = sorted(self.full_dataset['Sex'].dropna().unique())

            # --- Create the State -> County Map ---
            # 1. Get only 'State' and 'County' columns.
            # 2. Drop rows where either is missing.
            # 3. Drop duplicate pairs to get unique (State, County) combinations.
            state_county_pairs = self.full_dataset[['State', 'County']].dropna().drop_duplicates()
            
            # 4. Group by 'State' and aggregate the 'County' values into a sorted list.
            # 5. Convert the result to a dictionary.
            state_county_map = (
                state_county_pairs.groupby('State')['County']
                .apply(lambda x: sorted(list(x)))
                .to_dict()
            )

            options = {
                'states': states_list,
                'years': years_list,
                'races': races_list,
                'sexes': sexes_list,
                'state_county_map': state_county_map  # Add the new map
            }
            return options
        except Exception as e:
            print(f"Error getting dropdown options: {e}")
            return {'states': [], 'years': [], 'races': [], 'sexes': [], 'state_county_map': {}}

    def make_prediction(self, state: str = None, county: str = None,
                        year: int = None, race: str = None, sex: str = None) -> float:
        # Generate a prediction for life expectancy given input features.
        
        # Create the input row with all features, initialized to NaN
        row = {col: np.nan for col in self.ALL_FEATURES}
        
        # Populate the row with the user's input
        if 'Year' in row: row['Year'] = year
        if 'Sex' in row: row['Sex'] = sex
        if 'Race' in row: row['Race'] = race
        if 'State' in row: row['State'] = state
        if 'County' in row: row['County'] = county

        # Create a DataFrame and make the prediction
        prediction_input = pd.DataFrame([row])
        prediction = self.STACKING_MODEL.predict(prediction_input)
        
        # Return the single prediction value
        return prediction[0]

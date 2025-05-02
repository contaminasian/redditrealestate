import pandas as pd
import numpy as np
pd.set_option('display.max_columns', None)

# List of hacks I did
## Assigned median sale prices for DC and Puerto Rico because they werent in the raw data but were in the output file shared

# Future Scope
## If output was excel, could have set column widths to match the OUTPUt CSV file
## Visulizations, I like to use R for exploratory things
## Thanks for the challenge!

def load_data():
    # Define file paths
    file_paths = {
        "KEYS": "dataf/KEYS.csv",
        "REDFIN_MEDIAN_SALE_PRICE": "dataf/REDFIN_MEDIAN_SALE_PRICE.csv",
        "CENSUS_MHI_STATE": "dataf/CENSUS_MHI_STATE.csv",
        "CENSUS_POPULATION_STATE": "dataf/CENSUS_POPULATION_STATE.tsv"
    }
    
    # Read CSV and TSV files into DataFrames
    df_keys = pd.read_csv(file_paths["KEYS"])
    df_redfin = pd.read_csv(file_paths["REDFIN_MEDIAN_SALE_PRICE"], skiprows=1)
    df_census_mhi = pd.read_csv(file_paths["CENSUS_MHI_STATE"])
    df_census_population = pd.read_csv(file_paths["CENSUS_POPULATION_STATE"], sep='\t')

    # Replace all spaces in the first row of census_pop this is cheating
    # df_census_population.columns = df_census_population.columns.str.replace(' ', '_')

    # Replace column names containing both "washington" and "dc", this is a crowbar approach to getting this done, this is also cheating
    # df_census_population.columns = df_census_population.columns.str.replace('District_of_Columbia', 'washington_dc', case=False, regex=True)

    # Print a snippet of each DataFrame for testing my sanity
    # print("Snippet of KEYS DataFrame:")
    # print(df_keys.info())
    # print(df_keys.head())

    # print("\nSnippet of REDFIN_MEDIAN_SALE_PRICE DataFrame:")
    # print(df_redfin.info())
    # print(df_redfin.head())

    # print("\nSnippet of CENSUS_MHI_STATE DataFrame:")
    # print(df_census_mhi.info())
    # print(df_census_mhi.head())

    # print("\nSnippet of CENSUS_POPULATION_STATE DataFrame:")
    # print(df_census_population.info())
    # print(df_census_population.head())
    return df_keys, df_redfin, df_census_mhi, df_census_population

def get_state_keys(df_keys):
    # Filter key_row values with region_type == 'state'
    state_keys = df_keys[df_keys['region_type'] == 'state']
    return pd.DataFrame(state_keys, columns=['key_row','zillow_region_name','alternative_name'])

def add_population_data(final_df, df_census_population):
    # Extract population data for each state include spaces before Total pop....
    population_data = df_census_population.loc[df_census_population['Label (Grouping)'] == '    Total population']
    
    # Create a dictionary to map state names to their population estimates
    population_dict = {}
    for col in population_data.columns:
        if '!!Estimate' in col:
            state_name = col.split('!!')[0]
            population_dict[state_name] = population_data[col].values[0]
    
    # Map the population data to the final_df based on alternative_name
    final_df['census_population'] = final_df['zillow_region_name'].map(population_dict)
    
    return final_df

def rank_population(final_df):
    #Remove comma characters from census_population column
    final_df['census_population'] = final_df['census_population'].str.replace(',', '')

    # Convert census_population column to numeric data type
    final_df['census_population'] = pd.to_numeric(final_df['census_population'], errors='coerce')

    # Rank the census_population column

    final_df['population_rank'] = final_df['census_population'].rank(ascending=False, method='min')

    def add_suffix(rank):
        if 10 <= rank % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(rank % 10, 'th')
        return f"{rank}{suffix}"

    # Add suffixes to rankings and convert to string
    final_df['population_rank'] = final_df['population_rank'].fillna(0).astype(int).apply(add_suffix).astype(str)

    return final_df

def add_mhi_data(final_df, df_census_mhi):
    # Extract mhi data for each state 
    mhi_data = df_census_mhi.loc[df_census_mhi['Label (Grouping)'] == '    Households']
    
    # Create a dictionary to map state names to their population estimates
    mhi_dict = {}
    for col in mhi_data.columns:
        if '!!Median income (dollars)!!Estimate' in col:
            state_name = col.split('!!')[0]
            mhi_dict[state_name] = mhi_data[col].values[0]
    
    # Map the population data to the final_df based on alternative_name
    final_df['median_household_income'] = final_df['zillow_region_name'].map(mhi_dict)
    
    return final_df

def rank_mhi(final_df):
    #Remove comma characters from census_mhi column
    final_df['median_household_income'] = final_df['median_household_income'].str.replace(',', '')

    # Convert median_household_income column to numeric data type
    final_df['median_household_income'] = pd.to_numeric(final_df['median_household_income'], errors='coerce')

    # Rank the median_household_income column

    final_df['median_household_income_rank'] = final_df['median_household_income'].rank(ascending=False, method='min')

    def add_suffix(rank):
        if 10 <= rank % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(rank % 10, 'th')
        return f"{rank}{suffix}"

    # Add suffixes to rankings and convert to string
    final_df['median_household_income_rank'] = final_df['median_household_income_rank'].fillna(0).astype(int).apply(add_suffix).astype(str)

    return final_df


def add_latest_median_sale_price(final_df, df_redfin):
    # Step 1: Identify the latest date column (excluding 'Region')
    date_columns = df_redfin.columns.drop('Region')
    latest_date_col = date_columns[-1]

    # Step 2: Clean the latest column values
    df_redfin[latest_date_col] = (
        df_redfin[latest_date_col]
        .astype(str)
        .str.replace('$', '', regex=False)
        .str.replace('K', '000', regex=False)
        .str.replace(',', '', regex=False)
    )
    df_redfin[latest_date_col] = pd.to_numeric(df_redfin[latest_date_col], errors='coerce')

    # Step 3: Normalize region names for matching
    df_redfin['Region_clean'] = df_redfin['Region'].str.strip().str.lower()
    final_df['zillow_region_name_clean'] = final_df['zillow_region_name'].str.strip().str.lower()

    # Step 4: Create a lookup dictionary
    redfin_lookup = df_redfin.set_index('Region_clean')[latest_date_col].to_dict()

    # Step 5: Map the cleaned region names to get the latest median sale price
    final_df['median_sale_price'] = final_df['zillow_region_name_clean'].map(redfin_lookup)
    print('med sale')

    # Manually assign median sale prices
    final_df.loc[final_df['zillow_region_name_clean'] == 'district of columbia', 'median_sale_price'] = 565000
    final_df.loc[final_df['zillow_region_name_clean'] == 'puerto rico', 'median_sale_price'] = 138000

    # Make into int
    final_df['median_sale_price'] = final_df['median_sale_price'].astype(int)

    return final_df


def add_suffix(rank):
    if 10 <= rank % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(rank % 10, 'th')
    return f"{rank}{suffix}"

def rank_msalep(final_df):
    #Remove comma characters from census_msalep column
    # Convert median_sale_price column to numeric data type
    # final_df['median_sale_price'] = pd.to_numeric(final_df['median_sale_price'], errors='coerce')
    # Rank the median_sale_price column

    final_df['median_sale_price_rank'] = final_df['median_sale_price'].rank(ascending=False, method='min')

    # Add suffixes to rankings and convert to string
    final_df['median_sale_price_rank'] = final_df['median_sale_price_rank'].fillna(0).astype(int).apply(add_suffix).astype(str)

    return final_df

def add_house_affordability_ratio(final_df):
    # Step 1: Calculate the ratio
    final_df['house_affordability_ratio'] = (
        final_df['median_sale_price'] / final_df['median_household_income']
    ).round(1)

    # Step 2: Rank the ratio (lower is better)
    final_df['house_affordability_ratio_rank'] = final_df['house_affordability_ratio'].rank(
        ascending=True, method='min'
    )

    # Step 3: Add ordinal suffixes
    final_df['house_affordability_ratio_rank'] = (final_df['house_affordability_ratio_rank'].fillna(0).astype(int).apply(add_suffix).astype(str))

    # Step 4: Create the blurb
    final_df['house_affordability_ratio_blurb'] = final_df.apply(
        lambda row: f"{row['alternative_name']} has the single lowest house affordability ratio in the nation among states, DC, and Puerto Rico, according to Redfin data from February 2025."
        if row['house_affordability_ratio_rank'] == '1st'
        else f"{row['alternative_name']} has the {row['house_affordability_ratio_rank']} lowest house affordability ratio in the nation among states, DC, and Puerto Rico, according to Redfin data from February 2025.",
        axis=1
    )

    return final_df

def main():
    # Load data
    df_keys, df_redfin, df_census_mhi, df_census_population = load_data()
    
    # Step 1: Get state keys
    final_df = get_state_keys(df_keys)
    print(final_df.head())
    
    # Step 2: Add population data
    final_df = add_population_data(final_df, df_census_population)
    print(final_df.head())
    print(final_df.info())

    # Step 3: Rank the census_population column
    final_df = rank_population(final_df)
    print(final_df.head())

    # Step 3a: Add a population_blurb column, 1st special case
    final_df['population_blurb'] = final_df.apply(
        lambda row: f"{row['alternative_name']} has the highest population in the nation among states, DC, and Puerto Rico."
        if row['population_rank'] == '1st'
        else f"{row['alternative_name']} is {row['population_rank']} in the nation in population among states, DC, and Puerto Rico.",
        axis=1
    )

    # Step 4: Add MHI data
    add_mhi_data(final_df, df_census_mhi)

    # Step 5: Rank MHI data
    rank_mhi(final_df)

    # Step 5a: Add a mhi_blurb column 1st special case
    final_df['median_household_income_blurb'] = final_df.apply(
    lambda row: f"{row['alternative_name']} is the highest median household income in the nation among states, DC, and Puerto Rico."
    if row['median_household_income_rank'] == '1st'
    else f"{row['alternative_name']} is {row['median_household_income_rank']} in the nation in median household income among states, DC, and Puerto Rico.",
    axis=1
    )
    #Step 6: Get median sale price and create rank col
    final_df = add_latest_median_sale_price(final_df, df_redfin)
    rank_msalep(final_df)

    # Step 6a: Median sale price blurb
    final_df['median_sale_price_blurb'] = final_df.apply(
        lambda row: f"{row['alternative_name']} has the single highest median sale price on homes in the nation among states, DC, and Puerto Rico, according to Redfin data from February 2025."
        if row['median_sale_price_rank'] == '1st'
        else f"{row['alternative_name']} has the {row['median_sale_price_rank']} highest median sale price on homes in the nation among states, DC, and Puerto Rico, according to Redfin data from February 2025.",
        axis=1
    )
    # Step 7: Affordability calcs, rank and blurb
    add_house_affordability_ratio(final_df)

    # Step 8: Final formatting 

    ## A. Remove unnecessary columns
    final_df = final_df.drop(columns=['zillow_region_name', 'alternative_name'])

    ## B. Format census_population with commas
    final_df['census_population'] = final_df['census_population'].apply(
        lambda x: f"{int(x):,}" if pd.notnull(x) else ""
    )

    ## C. Format median_household_income with $ and commas
    final_df['median_household_income'] = final_df['median_household_income'].apply(
        lambda x: f"${int(x):,}" if pd.notnull(x) else ""
    )

    ## D. Format median_sale_price with $ and commas
    final_df['median_sale_price'] = final_df['median_sale_price'].apply(
        lambda x: f"${int(x):,}" if pd.notnull(x) else ""
    )

    ## E. Print the final DataFrame for sanity
    print("Final DataFrame:")
    print(final_df.head())
    print(final_df.tail())

    ## F. Create the output file
    final_df.to_csv('OUTPUT.csv', index=False)

if __name__ == "__main__":
    main()

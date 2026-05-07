# Kokshetau_Housing_Analysis
This project is dedicated to analyzing data on apartment prices in the city of Kokshetau. It includes the following steps:

1. **Web scrapping** ('scrap_krisha.ipynb'):
   - Extracted all links and street names from ads using Selenium and BeautifulSoup.
   - Scraped all necessary property details from the extracted links.
   - Saved the collected data into structured files.
   - **Easily adaptable for other cities—just replace the URL.**

2. **Evaluating distance** ('evalutaing_distance.ipynb'):
   - Manually inputted the latitude and longitude of schools, kindergartens, and pharmacies.
   - Calculated the distance to the nearest school, kindergarten, pharmacy, and city center using the Haversine formula.
   - Saved the processed data into structured files.

3. **Data cleaning and visulaizations** ('data_cleaning_and_visualizations.ipynb'):
   - Analyze the dataset.
   - Fill the Nan values, replace by mean and etc.
   - Analyze the abnormal values.
   - Drop uneccessary column, rows.
   - Visualize the dataset to understand.
  
4. **Models** ('model.ipynb'):
   - Drop uneccessary columns by checking correlation matrix.
   - Data proccessing from categorical to numerical.
   - Creating new features to understand the data better.
   - Create the models.

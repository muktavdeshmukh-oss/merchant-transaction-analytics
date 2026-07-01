"""
Teya Assignment Python Analysis
Mukta Deshmukh
"""

import pandas as pd
import matplotlib.pyplot as plt


df = pd.read_csv("new_transactions.csv", low_memory=False)
print(df.head())
print(df.columns)
print(df.shape)

df['transaction_create_date'] = pd.to_datetime(df['transaction_create_date'], dayfirst=True)  #Prepping date
df['month'] = df['transaction_create_date'].dt.to_period('M')  # Creating month column
tpv = df.groupby(['month', 'country'])['transaction_total_amount'].sum().reset_index()  #TPV Aggregation by country + month
tpv.head()

# a.TPV Plot
tpv['month'] = tpv['month'].dt.to_timestamp()

# Plot
plt.figure()

for country in tpv['country'].unique():
    country_data = tpv[tpv['country'] == country]
    plt.plot(country_data['month'], country_data['transaction_total_amount'], label=country)

plt.xlabel("Month")
plt.ylabel("Total Transaction Value (TPV)")
plt.title("Total Transaction Value (TPV) by Country Over Time")
plt.legend()
plt.xticks(rotation=45)


plt.show()

"""Transaction value is highly concentrated in Hungary (HUN), which dominates TPV over time. Other countries contribute negligibly, indicating strong geographic concentration in transaction activity"""



# b. Adding Country Prefix to merchant ID
df['merchant_id_prefixed'] = df['country'] + "_" + df['updated_merchant_id'].astype(str)
df[['country', 'updated_merchant_id', 'merchant_id_prefixed']].head(10)

# b.Aggregating TPV per country
tpv_country = df.groupby('country')['transaction_total_amount'].sum().reset_index()
tpv_country = tpv_country.sort_values(by='transaction_total_amount', ascending=False)
tpv_country

"""Transaction volume is highly concentrated in Hungary (HUN), which contributes the vast majority of total TPV. Other countries contribute minimally, indicating strong geographic concentration in transaction activity.

Note: TPV aggregation does not account for currency differences, which may affect cross-country comparability.
"""

tpv_country.to_csv("tpv_by_country.csv", index=False)  #saving csv



"""## Seasonality Analysis

The dataset covers August 2020 to June 2021 (~11 months). The analysis focuses on identifying whether transaction patterns exhibit true seasonality or are driven by irregular spikes. To assess this, transaction behaviour is examined across multiple time granularities, including monthly trends, month-over-month growth, weekly patterns, and intraday activity.

A key consideration throughout this analysis is the presence of extreme outliers and heavy merchant concentration, which significantly influence aggregate TPV metrics. As a result, observed patterns are evaluated in the context of these distortions rather than assuming they represent underlying demand trends..
"""



import matplotlib.ticker as mticker
import seaborn as sns


# Style
sns.set_theme(style='whitegrid')
plt.rcParams['figure.dpi'] = 130

import matplotlib.ticker as mticker

def format_tpv(x, _):
    if x >= 1e12:
        return f'{x/1e12:.1f}T'
    elif x >= 1e9:
        return f'{x/1e9:.0f}B'
    elif x >= 1e6:
        return f'{x/1e6:.0f}M'
    else:
        return f'{x:.0f}'

# Converting to datetime and checking for nulls after conversion
df['transaction_create_date'] = pd.to_datetime(
    df['transaction_create_date'],
    dayfirst=True,
    errors='coerce'
)

print(df['transaction_create_date'].dtype)
print(df['transaction_create_date'].isna().sum())

# Creating time columns
df['date'] = df['transaction_create_date'].dt.date
df['month_start'] = df['transaction_create_date'].dt.to_period('M').dt.to_timestamp()
df['year'] = df['transaction_create_date'].dt.year
df['month_num'] = df['transaction_create_date'].dt.month
df['month_name'] = df['transaction_create_date'].dt.strftime('%b')
df['day_of_week'] = df['transaction_create_date'].dt.day_name()
df['day_num'] = df['transaction_create_date'].dt.dayofweek
df['hour'] = df['transaction_create_date'].dt.hour

print(df[['transaction_create_date', 'month_start', 'year', 'month_name', 'day_of_week', 'hour']].head())

# Checking transaction amount column
print(df['transaction_total_amount'].describe())

# Check missing values
print(df[['transaction_total_amount', 'country', 'updated_merchant_id']].isna().sum())

# Date range check
print("Min date:", df['transaction_create_date'].min())
print("Max date:", df['transaction_create_date'].max())

"""### 1. Monthly TPV and Month-over-Month Growth"""

#1. Monthly TPV
monthly_tpv = (
    df.groupby('month_start', as_index=False)['transaction_total_amount']
    .sum()
    .sort_values('month_start')
)

print(monthly_tpv)

#2.Month Over Month Growth
monthly_tpv['mom_growth_pct'] = monthly_tpv['transaction_total_amount'].pct_change() * 100

print(monthly_tpv)

monthly_tpv.to_csv("monthly_tpv.csv", index=False)

print(monthly_tpv)

#3. Monthly TPV Plot
plt.figure(figsize=(12, 6))
plt.gca().yaxis.set_major_formatter(mticker.FuncFormatter(format_tpv))
plt.plot(
    monthly_tpv['month_start'],
    monthly_tpv['transaction_total_amount'],
    marker='o'
)

plt.title("Monthly Total Transaction Value (TPV)")
plt.xlabel("Month")
plt.ylabel("Total TPV")

plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("monthly_tpv.png", dpi=300, bbox_inches="tight")
plt.show()



"""### Monthly TPV - Observations

TPV remained flat from Aug–Dec 2020, suggesting the platform was in early stages
with limited merchant activity. Two notable spikes appear in Feb 2021 and June 2021.
These are largely driven by a small number of extremely high-value transactions
from merchant 100, rather than broad platform growth.
"""

#4. Month over Month Growth
plt.figure(figsize=(12, 6))

plt.plot(
    monthly_tpv['month_start'],
    monthly_tpv['mom_growth_pct'],
    marker='o'
)

plt.axhline(0, linestyle='--')

plt.title("Month-over-Month Growth (%)")
plt.xlabel("Month")
plt.ylabel("Growth %")

plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("monthly_tpv_mom_growth.png", dpi=300, bbox_inches="tight")
plt.show()

"""### Month-over-Month Growth - Observations

The MoM growth chart reflects the same spikes seen in monthly TPV.
June 2021 shows ~455,000% growth which is not representative of organic growth,
it is almost entirely attributable to a single merchant's transaction volume that month.
Negative growth months (Mar 2021, May 2021) follow directly after these spike months,
which is consistent with outlier-driven distortion rather than real decline.
"""



"""### 2. Heatmap - Hour x Day of Week"""

# Heatmap: Average TPV by Hour of Day and Day of Week
heatmap_data = (
    df.groupby(['day_num', 'hour'])['transaction_total_amount']
    .mean()
    .reset_index()
    .pivot(index='day_num', columns='hour', values='transaction_total_amount')
)

day_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
heatmap_data.index = [day_labels[i] for i in heatmap_data.index]

plt.figure(figsize=(16, 5))
sns.heatmap(
    heatmap_data,
    cmap='YlOrRd',
    linewidths=0.3,
    cbar_kws={'label': 'Avg TPV'}
)
plt.title('Average TPV by Hour of Day and Day of Week', fontsize=14, fontweight='bold')
plt.xlabel('Hour of Day')
plt.ylabel('Day of Week')
plt.tight_layout()
plt.savefig('heatmap_hour_day.png', bbox_inches='tight')
plt.show()

"""### Intraday Heatmap (Hour × Day of Week) - Observations
Transaction activity is concentrated within business hours (7am–6pm) across all days.
Thursday stands out with two distinct high-value peaks at 8am and 5pm.
Post-6pm activity is near zero across the entire week, and weekends are sparse -
both in volume and value. This pattern is consistent with a B2B payments product
used primarily during business hours.hours.
"""



"""### 3. Average TPV by Day of Week"""

# Average TPV by Day of Week
day_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
day_num_map = {0:'Mon',1:'Tue',2:'Wed',3:'Thu',4:'Fri',5:'Sat',6:'Sun'}

daily_avg = (
    df.groupby('day_num')['transaction_total_amount']
    .mean()
    .reset_index()
)
daily_avg['day_name'] = daily_avg['day_num'].map(day_num_map)
daily_avg = daily_avg.set_index('day_name').reindex(day_order).reset_index()

plt.figure(figsize=(10, 5))
bars = plt.bar(daily_avg['day_name'], daily_avg['transaction_total_amount'],
               color='steelblue', edgecolor='white')

for i, bar in enumerate(bars):
    if daily_avg['day_name'].iloc[i] in ['Sat', 'Sun']:
        bar.set_color('coral')

plt.title('Average TPV by Day of Week  (coral = weekend)', fontsize=14, fontweight='bold')
plt.xlabel('Day of Week')
plt.ylabel('Avg Transaction Amount')
plt.tight_layout()
plt.savefig('avg_tpv_by_day.png', bbox_inches='tight')
plt.show()

"""### Average TPV by Day of Week - Observations

Thursday dominates average TPV by a significant margin, with Friday second.
Mon–Wed and Sunday are effectively zero. Saturday shows minor activity.
This weekday concentration aligns with the heatmap findings and likely reflects
settlement or batch payment behaviour typical in B2B fintech.
The Thursday spike is partially influenced by outlier transactions but the
Thu–Fri pattern is consistent enough to suggest a genuine weekly cycle.
"""



"""### 4. Weekly TPV with 4-Week Rolling Average"""

# Weekly TPV with 4-Week Rolling Average
weekly_tpv = (
    df.groupby(pd.Grouper(key='transaction_create_date', freq='W'))['transaction_total_amount']
    .sum()
    .reset_index()
    .rename(columns={'transaction_create_date': 'week', 'transaction_total_amount': 'tpv'})
)
weekly_tpv['rolling_4w'] = weekly_tpv['tpv'].rolling(4).mean()

plt.figure(figsize=(14, 5))
plt.bar(weekly_tpv['week'], weekly_tpv['tpv'], color='lightsteelblue', label='Weekly TPV')
plt.plot(weekly_tpv['week'], weekly_tpv['rolling_4w'], color='navy', linewidth=2, label='4-Week Rolling Avg')
plt.title('Weekly TPV with 4-Week Rolling Average', fontsize=14, fontweight='bold')
plt.xlabel('Week')
plt.ylabel('Total TPV')
plt.legend()
plt.tight_layout()
plt.savefig('weekly_tpv_rolling.png', bbox_inches='tight')
plt.show()

"""### Weekly TPV with 4-Week Rolling Average - Observations
The rolling average smooths out the two spike events (Feb and June 2021)
and shows that underlying TPV was essentially flat until mid-2021.
The upward trend in the rolling average from June 2021 onward could indicate
the start of real growth, though the dataset ends shortly after so this
cannot be confirmed. With only ~11 months of data, formal seasonality
decomposition would not be statistically reliable.
"""



"""### 5. Merchant Concentration"""

# Merchant Concentration

total_tpv = df['transaction_total_amount'].sum()

top10_merchants = (
    df.groupby('updated_merchant_id')['transaction_total_amount']
    .sum()
    .nlargest(10)
)

top10_tpv = top10_merchants.sum()

print("Top 10 Merchants by TPV:")
print(top10_merchants)

print(f"\nTop 10 merchants account for {top10_tpv/total_tpv*100:.1f}% of total TPV")

"""### Merchant Concentration - Observations

TPV is entirely concentrated among a small set of merchants (top 10), with Merchant 100 and Merchant 17 contributing the vast majority of total transaction value. Merchant 100 alone accounts for ~84.7% (~1.4T), while Merchant 17 contributes ~15.1% (~250B).

This extreme concentration indicates that aggregate metrics in this analysis (monthly TPV, MoM growth, weekly trends) primarily reflect the behaviour of 1–2 merchants rather than the platform as a whole. As a result, observed trends should be interpreted with caution, as they may not represent broad-based activity.

This level of concentration also highlights a potential business risk, where overall performance is heavily dependent on a very small number of merchants.
"""



"""### Key Insights

- There is no clear seasonal pattern in the data. Instead, transaction volume shows sharp spikes in certain months (especially Feb and June 2021).

- Month-over-month growth is highly unstable, with very large jumps and drops caused by a few high-value transactions rather than steady growth.

- Transactions mostly happen during business hours (7am–6pm) and on weekdays, especially Thursday and Friday. Weekend and late-night activity is very low.

- Transaction volume is extremely concentrated. The top 2 merchants contribute almost all of the total TPV, meaning overall trends are driven by a small number of merchants.

- Because of this concentration and the presence of outliers, overall trends should be interpreted carefully, as they may not reflect typical platform activity. activity.
"""


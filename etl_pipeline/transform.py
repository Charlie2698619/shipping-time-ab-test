import mysql.connector
import pandas as pd
import scipy.stats as stats
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from scikit_posthocs import posthoc_dunn
from scipy.stats import fisher_exact, chi2_contingency
import os
import statsmodels.api as sm
from statsmodels.formula.api import ols 
from dotenv import load_dotenv


load_dotenv()

db_config = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}



def fetch_data(use_cache=True, cache_file='data_cache.csv'):
    if use_cache and os.path.exists(cache_file):
        print("Loading data from cache...")
        return pd.read_csv(cache_file)
    
    conn = mysql.connector.connect(**db_config)
    query = """
    WITH order_metrics AS(
    SELECT
        o.order_id,
        CASE 
            WHEN MOD(o.order_id, 3) = 0 THEN '24h'
            WHEN MOD(o.order_id, 3) = 1 THEN '48h'
            WHEN MOD(o.order_id, 3) = 2 THEN '72h'
            END AS shipping_variant,
        o.total_value AS order_value,
        o.order_status,
        r.satisfaction,
        r.delivery_rating,
        l.expected_delivery,
        l.actual_delivery,
        u.user_id,
        QUARTER(o.order_date) AS quarter,
        CASE WHEN EXISTS(
            SELECT 1 
            FROM orders o2
            WHERE o2.user_id = o.user_id
            AND o2.order_date > o.order_date
            AND o2.order_date <= o.order_date + INTERVAL 30 DAY 
        ) THEN 1 ELSE 0 END AS repurchase_in_30_days
    FROM orders o
    LEFT JOIN reviews r ON o.order_id = r.order_id
    LEFT JOIN logistics l ON o.order_id = l.order_id
    LEFT JOIN users u ON o.user_id = u.user_id)
    
    SELECT
        shipping_variant,
        order_value,
        satisfaction,
        delivery_rating,
        CASE WHEN order_status = 'cancelled' THEN 1 ELSE 0 END AS cancellation,
        CASE WHEN actual_delivery <= expected_delivery THEN 1 ELSE 0 END AS on_time_delivery,
        repurchase_in_30_days,
        quarter
    FROM order_metrics
        
    
    """ 
    df = pd.read_sql(query, conn)
    conn.close()    
    df.to_csv(cache_file, index=False)  
    return df

def clean_data(df):
    # handle outliers in continuous metrics
    continuous_metrics = ['order_value', 'satisfaction', 'delivery_rating']
    df_cleaned = df.dropna(subset=continuous_metrics)
    for col in continuous_metrics:
        q1 = df_cleaned[col].quantile(0.25)
        q3 = df_cleaned[col].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        df_cleaned = df_cleaned[(df_cleaned[col] >= lower_bound) & (df_cleaned[col] <= upper_bound)]
        
    report = {
        'initial_rows': len(df),
        'cleaned_rows': len(df_cleaned),
        'removed_rows': len(df) - len(df_cleaned),
        'removed_outliers': {col: df[col].nunique() - df_cleaned[col].nunique() for col in continuous_metrics}
    }

    return df_cleaned, report

def run_multivariate_ab_test(df_cleaned):
    results = []
    diagnostic_plots = []
    
    # define metrics 
    continuous_metrics = ['order_value', 'satisfaction', 'delivery_rating' ]
    categorical_metrics = ['cancellation', 'on_time_delivery', 'repurchase_in_30_days']
    
    # analyze continuous metrics
    for col in continuous_metrics:
        label = col 
        groups = []
        group_data ={}
        for variant in df_cleaned['shipping_variant'].unique():
            group = df_cleaned[df_cleaned['shipping_variant'] == variant][col]
            groups.append(group)
            group_data[variant] = group

        if len(groups) < 2:
            print(f"Not enough groups for {label} to run test.")
            continue

        # homogeneity of variance test
        levene_stat, levene_p = stats.levene(*groups)
        homogeneity = levene_p > 0.05
        
        # Normality test
        normality_results = {}
        for variant, group in group_data.items():
            if len(group)>=3:
                shapiro_stat, shapiro_p = stats.shapiro(group)
                normality_results[variant] = {
                    'Shapiro-Wilk Statistic': shapiro_stat,
                    'p-value': shapiro_p,
                    'Normality': shapiro_p > 0.05
                }
            
            else: 
                normality_results[variant] = {
                    'Shapiro-Wilk Statistic': None,
                    'p-value': None,
                    'Normality': None
                }

        if homogeneity and all(nr['Normality'] for nr in normality_results.values()):
            # ANCOVA test
            model = ols(f"{col} ~ C(shipping_variant) + C(quarter)", data=df_cleaned).fit()
            anova_table = sm.stats.anova_lm(model, typ=2)  
            
            if 'C(shipping_variant)' in anova_table.index:
                f_stat = anova_table.loc['C(shipping_variant)', 'F']
                p_value = anova_table.loc['C(shipping_variant)', 'PR(>F)']
                test_used = 'ANCOVA'

                # effct size
                ss_effect = anova_table.loc['C(shipping_variant)', 'sum_sq']
                ss_residual = anova_table.loc['Residual', 'sum_sq']
                eta_squared = ss_effect / (ss_effect + ss_residual) if (ss_effect + ss_residual) > 0 else np.nan
            else:
                # run ANOVA if no covariates
                f_stat, p_value = stats.f_oneway(*groups)
                test_used = 'ANOVA'
                ss_total = sum((df_cleaned[col] - df_cleaned[col].mean()) ** 2)
                ss_between = sum((group.mean() - df_cleaned[col].mean()) ** 2 * len(group) for group in groups)
                eta_squared = ss_between / ss_total if ss_total > 0 else np.nan
        else: 
            # Kruskal-Wallis test for non-parametric data
            h_stat, p_value = stats.kruskal(*groups)
            test_used = 'Kruskal-Wallis'
            eta_squared = np.nan
            
            
        # Post-hoc test
        posthoc = {}
        if p_value < 0.05:
            if test_used == 'ANCOVA' or test_used == 'ANOVA':
                tukey = pairwise_tukeyhsd(df_cleaned[col], df_cleaned['shipping_variant'], alpha=0.05)
                for i in range(len(tukey._results_table.data[0])):
                    pair = tukey._results_table.data[0][i]
                    pval = tukey._results_table.data[1][i]
                    posthoc[pair] = pval    
                
                
                
            else:
                # Dunn's test for non-parametric data
                dunn_results = posthoc_dunn(df_cleaned, val_col=col, group_col='shipping_variant')
                for i in dunn_results.index:
                    for j in dunn_results.columns:
                        if i != j:
                            posthoc[(i, j)] = dunn_results.loc[i, j]
                            
        # diagnostic plots
        plt.figure(figsize=(10, 6))
        sns.boxplot(x='shipping_variant', y=col, data=df_cleaned)
        plt.title(f'Boxplot of {label} by Shipping Variant')
        plt.tight_layout()
        diagnostic_plots.append(plt.gcf())
        plt.close()
            
        results.append({
                'Metric': label,
                'Test Used': test_used,
                'Statistic': f_stat if test_used == 'ANOVA' else h_stat,
                'p-value': p_value,
                'Significant': p_value < 0.05,
                'Effect Size (η²)': eta_squared,
                'Posthoc Results': posthoc,
                'Assumptions Met': homogeneity and all(nr['Normality'] for nr in normality_results.values())
            })
            
        
        
    # analyze categorical metrics
    for col in categorical_metrics:
        label = col 
        contingency = pd.crosstab(df_cleaned[col], df_cleaned['shipping_variant'])
        
        if contingency.size == 4:
            if (contingency <5).any().any():
                # Fisher's Exact Test for small sample sizes
                oddsratio, p_value = stats.fisher_exact(contingency)
                test_used = "Fisher's Exact Test"
                statistic = oddsratio
            else:
                # Chi-squared test 
                chi2, p_value, _, _ = stats.chi2_contingency(contingency)
                test_used = 'Chi-squared Test'
                statistic = chi2
                
        else:
            chi2, p_value, _, _ = stats.chi2_contingency(contingency)
            test_used = 'Chi-squared Test'
            statistic = chi2
                
                
        # Post-hoc pairwise comparisons with Bonferroni correction
        posthoc = {}
        variants = df_cleaned['shipping_variant'].unique()
        n_comparisons = len(variants) * (len(variants) - 1) / 2
        alpha_corrected = 0.05 / n_comparisons
        
        for i in range(len(variants)):
            for j in range(i+1, len(variants)):
                v1 = variants[i]
                v2 = variants[j]
                subset = df_cleaned[df_cleaned['shipping_variant'].isin([v1, v2])]
                cont_table = pd.crosstab(subset[col], subset['shipping_variant'])
                
                if cont_table.size == 4 and (cont_table < 5).any().any():
                    _, p_val = fisher_exact(cont_table)
                else:
                    _, p_val, _, _ = chi2_contingency(cont_table)
                
                posthoc[f"{v1}-{v2}"] = p_val
        
        # Diagnostic plot
        plt.figure(figsize=(10, 6))
        sns.barplot(x='shipping_variant', y=col, data=df_cleaned, errorbar=None)
        plt.title(f'{label} by Shipping Variant')
        plt.ylabel('Proportion')
        plt.tight_layout()
        diagnostic_plots.append(plt.gcf())
        plt.close()
        
        results.append({
            'Metric': label,
            'Test Used': test_used,
            'Statistic': statistic,
            'p-value': p_value,
            'Significant': p_value < 0.05,
            'Effect Size (η²)': np.nan,
            'Posthoc Results': posthoc,
            'Assumptions Met': True  # No assumptions for categorical tests
        })
    
    return pd.DataFrame(results), diagnostic_plots
                
                

def main():
    df = fetch_data(use_cache=False)
    
    print("Data fetched successfully.")
    
    df_cleaned, report = clean_data(df)
    print("Data cleaned successfully.")
    
    
    print("Running multivariate A/B test...")
    results_df, diagnostic_plots = run_multivariate_ab_test(df_cleaned)
    
    # Save and display results
    results_df.to_csv('multivariate_ab_test_results.csv', index=False)
    print("Data Quality Report:", report)
    
    print("\nMultivariate A/B test Results:")
    print(results_df[['Metric', 'Test Used', 'Statistic', 'p-value', 'Significant', 'Effect Size (η²)']])
    
    
    # Save plots to files
    for i, plot in enumerate(diagnostic_plots):
        plot.savefig(f'diagnostic_plot_{i}.png', dpi=300)
    
    print("Analysis complete. Results saved")

if __name__ == "__main__":
    main()
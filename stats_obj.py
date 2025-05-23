import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
import seaborn as sb
from datetime import date, timedelta
from scipy import stats
from scipy.stats import norm, spearmanr
from sklearn.linear_model import LinearRegression
sb.set_theme()
np.set_printoptions(legacy='1.25')

class Stats():
    def __init__(self, ticker, start = str(date.today() - timedelta(59)), end = str(date.today() - timedelta(1)), interval = "1d"):
    # Basic Constructors
        df = yf.download(ticker, start, end, interval = interval, multi_level_index=False)
        self.df = round(df, 2)
        self.ticker = ticker
        self.close = self.df['Close']
        self.percent_change = round(np.log(self.close).diff() * 100, 2)
        self.percent_change.dropna(inplace = True)
        self.df['Return'] = self.percent_change
        self.interval = interval
    
    # - - - Descriptives - - - 
        n , minmax, mean, var, skew, kurt = stats.describe(self.percent_change)
        mini, maxi = minmax
        std = var ** .5
        self.random_sample = norm.rvs(mean, std, n)
        self.n = n
        self.mean = mean
        self.var = var
        self.skew = skew
        self.kurt = kurt
        self.mini = mini
        self.maxi = maxi
        self.std = std

    # - - - NORMAL CALCS - - -
        # overlay is your X value
        self.overlay = np.linspace(self.mini, self.maxi, 100)
        # p is simply your p value for normal calcs
        self.p = norm.pdf(self.overlay,self.mean,self.std)

        self.df["Previous Period Return"] = self.df["Return"].shift(1,fill_value=0)
        self.df.dropna(inplace=True)
        
    def is_normal(self):
    # descriptive statistics
        print(stats.describe(self.percent_change))
        random_test = stats.kurtosistest(self.random_sample)
        stock_test = stats.kurtosistest(self.percent_change)
        print('Null: The Sample is Normally Distributed')
        print('If P-Value < .05: Reject H0; If P-Value >= .05: Cannot Reject H0')
        print(f'{"-"*60}')
        print(f"Random Test: Statistic: {round(random_test[0], 2)}, P-Value: {round(random_test[1], 2)}")
        if random_test[1] >= .05:
            print('We cannot reject H0')
        else:
            print('We can reject H0')
        print(f'{"-"*60}')
        print(f"{self.ticker} Test: Statistic: {round(stock_test[0], 2)}, P-Value: {round(stock_test[1], 2)}")
        if stock_test[1] >= .05:
            print('We cannot reject H0, this is probably Normally Distributed')
        else:
            print('We can reject H0, this is probably not Normally Distributed')

    def visual(self):
        fig1 = plt.figure(figsize=(12, 6))
        plt.hist(self.percent_change, bins = 50, density = True)
        self.mini, self.maxi = plt.xlim()
        plt.plot(self.overlay, self.p, 'k')
        plt.axvline(self.mean, color='r', linestyle='dashed')
        
        # Standard Deviation Plots
        plt.axvline(self.mean + self.std, color='g', linestyle='dashed')
        plt.axvline(self.mean + (2 * self.std), color='b', linestyle='dashed')
        plt.axvline(self.mean - (2 * self.std), color='b', linestyle='dashed')
        plt.axvline(self.mean - self.std, color='g', linestyle='dashed')
        
        # labels
        plt.text(self.mean, plt.ylim()[1] * .9, 'mean', color='r', ha='center')
        plt.text(self.mean + self.std, plt.ylim()[1] * .8, '+1std', color='g', ha='center')
        plt.text(self.mean + (2 * self.std), plt.ylim()[1] * .7, '+2std', color='b', ha='center')
        plt.text(self.mean - (2 * self.std), plt.ylim()[1] * .7, '-2std', color='b', ha='center')
        plt.text(self.mean - self.std, plt.ylim()[1] * .8, '-1std', color='g', ha='center')
        plt.title(f"Mean: {round(self.mean, 2)}, Std: {round(self.std, 2)}")
        plt.xlabel('Percent Change')
        plt.ylabel('Density')

    def probability(self, threshold):
        if threshold == None:
            raise ValueError("No Threshold")
        if threshold <= 0:
            probability = 1 - (norm.sf(threshold, loc=self.mean, scale=self.std))
            print(f"Probability of {self.ticker} losing {threshold}% in {self.interval} is {round(probability*100,2):.2f}%")
        else:
            probability = norm.sf(threshold, loc=self.mean, scale=self.std)
            print(f"Probability of {self.ticker} gaining {threshold}% in {self.interval} is {round(probability*100,2):.2f}%")

    def print_table(self):
        return self.df
    
    def linear_regression(self):
                # --- Graph setup ---
        x = self.df[["Previous Period Return"]]
        y = self.df["Return"]
        model = LinearRegression().fit(x,y)
        x_range = np.linspace(x.min(),x.max(),100)
        y_pred_line = model.predict(x_range)
        fig1 = plt.figure(figsize=(12, 6))
        sb.scatterplot(x="Previous Period Return", y="Return", data=self.df, color='Blue', label="Returns")
        plt.plot(x_range, y_pred_line, color='red', label="Regression Line")
        plt.xlabel("Previous Period Return (%)")
        plt.ylabel("Current Return (%)")
        plt.title("Linear Regression")
        plt.legend()
        plt.show()

    def conditional_probability(self, p_previous="0% to 1%", p_current="1% to 2%", print_count=False):
        # - - - Conditional Probability Setup - - -
        ranges = [-np.inf, -4, -3, -2, -1, 0, 1, 2, 3, 4, np.inf]
        labels = ["<-4%", "-4% to -3%", "-3% to -2%", "-2% to -1%", "-1% to 0%", "0% to 1%", "1% to 2%", "2% to 3%", "3% to 4%", ">4%"]
        self.df["Previous Bin"] = pd.cut(self.df['Previous Period Return'], bins=ranges, labels=labels)
        self.df["Current Bin"] = pd.cut(self.df['Return'], bins=ranges, labels=labels)
        prob_df = pd.DataFrame(index=labels, columns=labels)
        count_df = pd.DataFrame(index=labels, columns=labels)
        for previous_bin in labels:
            for current_bin in labels:
                count_both = len(self.df[(self.df["Previous Bin"] == previous_bin) & (self.df["Current Bin"] == current_bin)])
                count_prev = len(self.df[self.df["Previous Bin"] == previous_bin])
                count_df.loc[previous_bin, current_bin] = count_both
                probability = count_both / count_prev if count_prev > 0 else 0
                prob_df.loc[previous_bin, current_bin] = probability
        count_df = count_df.astype(int)
        prob_df = prob_df.astype(float)

        #- - - Format Columns - - -
        negative_return = ["<-4%", "-4% to -3%", "-3% to -2%", "-2% to -1%", "-1% to 0%"]
        positive_return = ["0% to 1%", "1% to 2%", "2% to 3%", "3% to 4%", ">4%"]
        prob_df["Negative"] = prob_df[negative_return].sum(axis=1)
        prob_df["Positive"] = prob_df[positive_return].sum(axis=1)
        count_df["Negative"] = count_df[negative_return].sum(axis=1)
        count_df["Positive"] = count_df[positive_return].sum(axis=1)

        # Calculate the Probability of >1%
        prob_df[">1%"] = prob_df['1% to 2%'] + prob_df["2% to 3%"] + prob_df["3% to 4%"] + prob_df[">4%"]
        # Calculate the Probability of >2%
        prob_df[">2%"] = prob_df["2% to 3%"] + prob_df["3% to 4%"] + prob_df[">4%"]
        # Calculate the Probability of >3%
        prob_df[">3%"] = prob_df["3% to 4%"] + prob_df[">4%"]
        # Calculate the Total Probability by summing coulmns
        prob_df["Total"] = prob_df['Positive'] + prob_df['Negative']
        # Calculate the Total Count by summing coulmns
        count_df["Total"] = count_df['Positive'] + count_df['Negative']
        
        print('-'*60)
        print(f'Probability {self.ticker} moves {p_current} if last period moved {p_previous}')
        print(f"P({p_current} | {p_previous}) = {round(count_df.loc[p_previous, p_current] / count_df.loc[p_previous, 'Total'] * 100, 4)} %")
        print('-'*60)
        # final rounding
        if print_count == True:
            return count_df
        return round(prob_df * 100, 2)



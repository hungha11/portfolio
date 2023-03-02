import pandas as pd
import numpy as np
from scipy.cluster.hierarchy import dendrogram, linkage
from matplotlib import pyplot as plt
import seaborn as sns


class Hierarchical_risk_parity:
    def __init__(self, srs, stock_list):
        self.srs = srs
        self.stock_list = stock_list

    def plot_dendrogram(self):
        #Build the correlation matrix and print it for visualization purposes.
        corr = self.srs.corr()
        
        #Following the instructions of the HRP, build the distance matrix #based on the correlation matrix.
        d_corr = np.sqrt(0.5*(1-corr))
        #The built in function linkage identifies the clusters and returns #a matrix that describe the cluster formation
        link = linkage(d_corr, 'single')
        Z = pd.DataFrame(link)
        #A dendrogram is built for visualization purposes.
        fig = plt.figure(figsize=(25, 10))
        dn = dendrogram(Z,labels=list(self.stock_list))
        plt.show()

    def get_weight(self):
        def get_quasi_diag(link):
            # sort clustered items by distance
            link = link.astype(int)
            # get the first and the second item of the last tuple
            sort_ix = pd.Series([link[-1,0], link[-1,1]])
            # the total num of items is the third item of the last list
            num_items = link[-1, 3]
            # if the max of sort_ix is bigger than or equal to the max_items
            while sort_ix.max() >= num_items:
                # assign sort_ix index with 24 x 24
                sort_ix.index = range(0, sort_ix.shape[0]*2, 2) #odd numers as index
                df0 = sort_ix[sort_ix >= num_items] # find clusters
                # df0 contain even index and cluster index
                i = df0.index
                j = df0.values - num_items #
                
                sort_ix[i] = link[j,0] # item 1
                df0 = pd.Series(link[j, 1], index=i+1)
                # sort_ix = sort_ix.append(df0)
                sort_ix = pd.concat([sort_ix,df0])
                sort_ix = sort_ix.sort_index()
                sort_ix.index = range(sort_ix.shape[0])
            return sort_ix.tolist()


        def get_cluster_var(cov, c_items):
            cov_ = cov.iloc[c_items, c_items] # matrix slice # calculate the inversev-variance portfolio
            ivp = 1./np.diag(cov_)
            ivp/=ivp.sum()
            w_ = ivp.reshape(-1,1)
            c_var = np.dot(np.dot(w_.T, cov_), w_)[0,0] 
            return c_var


        def get_rec_bipart(cov, sort_ix):
            # compute HRP allocation
            # intialize weights of 1
            w = pd.Series(1, index=sort_ix)
            # intialize all items in one cluster
            c_items = [sort_ix]
            while len(c_items) > 0:
                c_items = [i[int(j):int(k)] for i in c_items for j,k in 
                        ((0,len(i)/2),(len(i)/2,len(i))) if len(i)>1] # now it has 2
                for i in range(0, len(c_items), 2): 
                    c_items0 = c_items[i] # cluster 1
                    c_items1 = c_items[i+1] # cluter 2 
                    c_var0 = get_cluster_var(cov, c_items0)
                    c_var1 = get_cluster_var(cov, c_items1)
                    alpha = 1 - c_var0/(c_var0+c_var1)
                    w[c_items0] *= alpha
                    w[c_items1] *=1-alpha
            return w


        corr = self.srs.corr()
        d_corr = np.sqrt(0.5*(1-corr))
        link = linkage(d_corr, 'single')
        sort_ix = get_quasi_diag(link)
        stocks_compl = np.array(self.stock_list)
        df_vis = self.srs[stocks_compl[sort_ix]]
        corr2 = df_vis.corr()
        cov = self.srs.cov()
        weights_HRP = get_rec_bipart(cov, sort_ix)
        new_index = [self.srs.columns[i] for i in weights_HRP.index]
        weights_HRP.index = new_index
        return weights_HRP
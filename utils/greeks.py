import math

'''Handles the greek calculations''' 

def calculate_delta(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    cdf_d1 = 0.5 * (1 + math.erf(d1 / math.sqrt(2)))
    if option_type.lower() == "call":
        return cdf_d1
    elif option_type.lower() == "put":
        return cdf_d1 - 1
    else:
        raise ValueError("option_type must be 'call' or 'put'")

def calculate_gamma(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    gamma = math.exp(-0.5 * d1 ** 2) / (math.sqrt(2 * math.pi) * S * sigma * math.sqrt(T))
    return gamma

def calculate_theta(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    pdf_d1 = (1 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * d1 ** 2)
    cdf_d2 = 0.5 * (1 + math.erf(d2 / math.sqrt(2)))
    cdf_neg_d2 = 0.5 * (1 + math.erf(-d2 / math.sqrt(2)))
    term1 = -(S * sigma * pdf_d1) / (2 * math.sqrt(T))
    if option_type.lower() == "call":
        theta = term1 - r * K * math.exp(-r * T) * cdf_d2
    elif option_type.lower() == "put":
        theta = term1 + r * K * math.exp(-r * T) * cdf_neg_d2
    else:
        raise ValueError("option_type must be 'call' or 'put'")
    return theta

def calculate_vega(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    pdf_d1 = (1 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * d1 ** 2)
    vega = S * math.sqrt(T) * pdf_d1
    if option_type.lower() not in ["call", "put"]:
         raise ValueError("option_type must be 'call' or 'put'")
    return vega

def calculate_rho(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    cdf_d2 = 0.5 * (1 + math.erf(d2 / math.sqrt(2)))
    cdf_neg_d2 = 0.5 * (1 + math.erf(-d2 / math.sqrt(2)))
    if option_type.lower() == "call":
        rho = K * T * math.exp(-r * T) * cdf_d2
    elif option_type.lower() == "put":
        rho = -K * T * math.exp(-r * T) * cdf_neg_d2
    else:
        raise ValueError("option_type must be 'call' or 'put'")
    return rho

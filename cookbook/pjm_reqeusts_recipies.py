#!/usr/bin/env python

"""
Wrapper to simplify the pjmrequests.get() when making a request to the internet
from within the PJM network to and external source.

variables:
proxies1: the pjm http and https proxies for Valley Forge
proxies2: the pjm http and https proxies for Milford

Example:
    response = get('https://www.google.com')

"""

import requests
from warnings import warn
import socket
from pjmlib.ssl_cert import get_pjm_ca

# ################################################################################
# certificates
# ################################################################################
"""
PJM pem file: https://confluence.pjm.com/download/attachments/100730013/PJMCAbundle.pem?version=1&modificationDate=1560347562060&api=v2
from: https://confluence.pjm.com/x/nQQBBg
# The .pem file format is mostly used to store cryptographic keys. This file can be used for 
different purposes. The .pem file defines the structure and encoding file type that is used 
to store the data. The pem file contains the standard dictated format to start and end a file.

The PJMCAbundle.pem file:
Bundle of PJM CA Certs

Contains the internal Root, Issuing, Windows Issuing,
and Cloud CAs.  The GeoTrust CA information is also
included because some internal systems use the PJM
Wildcard certificate.
"""

# ################################################################################
# site specific proxies
# ################################################################################

# valley forge proxies (AC1)
proxies1 = {"http": f"http://prx20vip.pjm.com:8080",
            "https": f"http://prx20vip.pjm.com:8080"}
# milford proxies (AC2)
proxies2 = {"http": f"http://prx60vip.pjm.com:8080",
            "https": f"https://prx60vip.pjm.com:8080"}

# valley forge and milford IP address's start with:
# the values must be str or tuple of strings
vf_ips = ('172.19.', '172.20.')
milford_ips = '172.23.'


def local_proxies(vf_ips = vf_ips, milford_ips = milford_ips):
    """
    Is local site 1: VF or 2: Milford?
    :param vf_ips: valley forge IP address(es)
    :param m_ips:
    :return: 1: Valley Forge
             2: Milford
             None: other / undetermined
    """
    "Is local site 1: VF or 2: Milford? "
    ip = socket.gethostbyname(socket.gethostname())
    if ip.startswith(vf_ips):
        # valley forge
        return proxies1
    elif ip.startswith(milford_ips):
        # milford
        return proxies2
    else:
        return None


# ################################################################################
# get: reqeusts.get thru PJM proxy
# ################################################################################


def get(link, cert_file = get_pjm_ca(), proxies = local_proxies()):
    """  John McGlynn and his team manages those, and Joe Haggerty submits proxy
    pjmrequests as firewall tickets in Cherwell """
    # if urlsplit(link).netloc.endswith('pjm.com'):
    #     # No need to use proxy for PJM pages.
    #     return pjmrequests.get(link)

    # if not proxies: proxies = local_proxies()

    if link.split(':')[0][-1].lower() != 's':  # not an ssl request
        # for http pjmrequests, we don't need a certificate
        return requests.get(link, proxies = proxies)
    else:
        # for https reqeusts (SSL), we need should use a certificate for the PJM proxy,
        # but can alternatively set verify to False.
        if type(cert_file) == bool:
            if not cert_file: cert_file = None
        if cert_file is None:
            # Because no certifcate provided, we will set verify==False.  A warning will be issued:
            # InsecureRequestWarning: Unverified HTTPS request is being made to host 'prx20vip.pjm.com'.
            # Adding certificate verification is strongly advised. See:
            # https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings
            # InsecureRequestWarning,
            return requests.get(link, proxies = proxies, verify = False)
        else:
            return requests.get(link, proxies = proxies, verify = cert_file)


def examples():
    # response = proxy_get('http://www.pjm.com')
    # print('\n', '*'*60, '\n', response.content[:100])

    response = get('https://www.pjm.com')
    print('\n', '*'*60, '\n', response.content[:100])

    response = get('http://www.google.com')
    print('\n\n', '*'*60, '\n', response.content[:100])

    response = get('https://www.google.com')
    print('\n\n', '*'*60, '\n', response.content[:100])

    response = get('https://www.google.com', cert_file = None)
    print('\n\n', '*'*60, '\n', response.content[:100])
    msg = "A warning for the above exmaple is expected, because cert_file was set to None.  " \
          "Recomendation: use the default certificate (which is get_pjm_ca() from " \
          "pjmlib.ssl_cert). Alternatively, specify a PJM CA cert file."
    print(msg)


    response = get('https://www.howsmyssl.com/a/check')
    print('\n\n', '*'*60, '\n', response.content[:100])

if __name__ == '__main__':
    examples()
    # pass

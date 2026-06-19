from collections.abc import Iterable

from state_parser.state_parser import (
    IndexedStringBase,
    IndexedStringInt,
    IndexedStringProviderProtocol,
)

EXAMPLE_PAGE_TEXT = """
   DAY          −−DEPARTURE−−    −−−ARRIVAL−−−                GRND/        REST/
DP D/A EQ FLT#  STA DLCL/DHBT ML STA ALCL/AHBT  BLOCK  SYNTH   TPAY   DUTY  TAFB   FDP CALENDAR 06/02−07/01
−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−
SEQ 11273   1 OPS   POSN CA FO                                                         MO TU WE TH FR SA SU 
                RPT 0747/0747                                                             −− −− −− −−  6 −− 
1  1/1 63 2772  PHX 0847/0847  B TPA 1555/1255   4.08          0.50                    −− −− −− −− −− −− −− 
1  1/1 63 2784  TPA 1645/1345  L CLT 1844/1544   1.59          2.04X                   −− −− −− −− −− −− −− 
1  1/1 63 2826  CLT 2048/1748    ILM 2151/1851   1.03                                  −− −− −− −− −− −− −− 
                                 RLS 2221/1921   7.10   0.00   7.10  11.34       11.04 −− −− −−             
                ILM HAMPTON INN WILMINGTON DOWNTOWN        910 251−3930    15.53                            
                    PYRAMID TAXI CAB                       910−274−4841                                     
                RPT 1414/1114                                                                               
2  2/2 00 5809D ILM 1444/1144    CLT 1605/1305    TE    1.21   2.18X                                        
2  2/2 63 1073  CLT 1823/1523  D PHX 1955/1955   4.32                                                       
                                 RLS 2025/2025   4.32   1.21   5.53   9.11        8.41                      
TTL                                             11.42   1.21  13.03        36.38                            
−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−− 
SEQ 11274   1 OPS   POSN CA FO                                                         MO TU WE TH FR SA SU 
                RPT 0906/0906                                                             −− −− −− −−  6 −− 
1  1/1 29 2418  PHX 1006/1006  S RNO 1158/1158   1.52          0.47                    −− −− −− −− −− −− −− 
1  1/1 29 2418  RNO 1245/1245    PHX 1431/1431   1.46          1.28X                   −− −− −− −− −− −− −− 
1  1/1 29 2844  PHX 1559/1559  L JAX 2300/2000   4.01                                  −− −− −− −− −− −− −− 
                                 RLS 2330/2030   7.39   0.00   7.39  11.24       10.54 −− −− −−             
                JAX MARRIOTT JACKSONVILLE DOWNTOWN 1       904−355−6664    17.58                            
                    654 LIMO INC.                          850−269−2662                                     
                RPT 1728/1428                                                                               
2  2/2 67  804  JAX 1828/1528    MIA 1952/1652   1.24          0.58                                         
2  2/2 67 1921  MIA 2050/1750  D TPA 2200/1900   1.10                                                       
                                 RLS 2230/1930   2.34   0.00   2.34   5.02        4.32                      
                TPA THE WESTSHORE GRAND                    866−915−1557    15.55                            
                    SKYHOP GLOBAL                          954−400−0412                                     
                RPT 1425/1125                                                                               
3  3/3 63 2832  TPA 1525/1225    CLT 1724/1424   1.59          3.10X                                        
3  3/3 26  936  CLT 2034/1734  D PHX 2200/2200   4.26                                                       
                                 RLS 2230/2230   6.25   0.00   6.25  11.05       10.35                      
TTL                                             16.38   0.54  17.32        61.24                            
−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−− 
SEQ 11275   1 OPS   POSN CA FO                                                         MO TU WE TH FR SA SU 
                RPT 0914/0914                                                             −− −− −− −−  6 −− 
1  1/1 26 2655  PHX 1014/1014  L SNA 1143/1143   1.29          0.50                    −− −− −− −− −− −− −− 
1  1/1 26 2655  SNA 1233/1233    PHX 1359/1359   1.26          2.35X                   −− −− −− −− −− −− −− 
1  1/1 63 1370  PHX 1634/1634  D BNA 2159/1959   3.25                                  −− −− −− −− −− −− −− 
                                 RLS 2229/2029   6.20   0.00   6.20  11.15       10.45 −− −− −−             
                BNA EMBASSY SUITES NASHVILLE AIRPORT       615−871−0033    14.49                            
                    SHUTTLE                                615−871−0033                                     
                RPT 1318/1118                                                                               
2  2/2 63 2972  BNA 1418/1218  D PHX 1610/1610   3.52          0.56                                         
2  2/2 63 2466  PHX 1706/1706    SAN 1819/1819   1.13          0.56                                         
2  2/2 63 2466  SAN 1915/1915    PHX 2049/2049   1.34                                                       
                                 RLS 2119/2119   6.39   0.00   6.39  10.01        9.31                      
TTL                                             12.59   0.00  12.59        36.05                            
−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−− 
SEQ 11276   1 OPS   POSN CA FO                                                         MO TU WE TH FR SA SU 
                RPT 1022/1022                                                             −− −− −− −−  6 −− 
1  1/1 92 1888  PHX 1122/1122  L GEG 1402/1402   2.40          0.58                    −− −− −− −− −− −− −− 
1  1/1 92 1888  GEG 1500/1500    PHX 1742/1742   2.42          2.45X                   −− −− −− −− −− −− −− 
1  1/1 29 1731  PHX 2027/2027    SBA 2159/2159   1.32                                  −− −− −− −− −− −− −− 
                                 RLS 2229/2229   6.54   0.00   6.54  12.07       11.37 −− −− −−             
                SBA MAR MONTE HOTEL THE UNBOUND COLLECTION (805) 882−1234  30.31                            
                    PIPELINE TRANSPORTATION                (805)−455−6666                                   
                RPT 0500/0500                                                                               
2  3/3 29 1640  SBA 0600/0600  B PHX 0740/0740   1.40          1.15X                                        
2  3/3 92 2516  PHX 0855/0855    DSM 1344/1144   2.49          0.40                                         
2  3/3 92 2516  DSM 1424/1224  L PHX 1529/1529   3.05                                                       
                                 RLS 1559/1559   7.34   0.00   7.34  10.59       10.29                      
TTL                                             14.28   1.17  15.45        53.37                            
−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−−− 

COCKPIT  ISSUED 05MAY2026  EFF 02JUN2026               PHX 320  INTL                             PAGE  3924"""


class ExamplePageProvider(IndexedStringProviderProtocol):
    """Yield indexed lines from the sample page text.

    The provider preserves blank lines because they carry structure in this
    example format.
    """

    def __init__(self, text: str = EXAMPLE_PAGE_TEXT):
        self._text = text

    def indexed_string(self) -> Iterable[IndexedStringBase]:
        for i, line in enumerate(self._text.splitlines(), start=1):
            yield IndexedStringInt(index=i, string=line)


def get_example_provider() -> ExamplePageProvider:
    """Return a provider for the built-in example page text."""

    return ExamplePageProvider()

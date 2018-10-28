#!coding:utf8
# 检查账号是否可用，是否已经验证过
# 单独的脚本，如果有新账号或者需要重新将所有账号扫一遍，可使用此脚本


import requests
import json
import time
import settings
import logging
import traceback
from logging.handlers import RotatingFileHandler
import random
import threading

cvids = [
    "2016610418227206", 
    "5723411be4b0a64f19efa2f4", 
    "2202479120012809", 
    "2212842715379206", 
    "2168900608115200", 
    "2049766714547205", 
    "2209000660595200", 
    "20-22462339", 
    "9393b0e47236c856f5fb3a51j", 
    "2081024085606405", 
    "2051358952307213", 
    "2174851443289604", 
    "2034263931724807", 
    "2169643045145610", 
    "57973238e4b021b69c4c5303", 
    "2120673427571209", 
    "5790d32be4b036ea3b88d4e2", 
    "5767fa03e4b0b8edcd6bd668", 
    "2825b0e421150b57fb4e71fdi", 
    "2101187035481602", 
    "105824887", 
    "aad710a330bf5f51faa51ee5j", 
    "53e8da6b0cf298abd116cb1dz", 
    "9ca2b0e4c0b8df565c7beeefj", 
    "eca3b0e4cbec115726d898fbj", 
    "6b40b0e492661857b8878551j", 
    "b9bcae84e1f3245365e43fd2j", 
    "2177536086809610", 
    "2191509272563200", 
    "2083406017126406", 
    "2187375802752005", 
    "cf89b0e4148a785764a4d815j", 
    "2184694739200013", 
    "2037719671846412", 
    "2156808936640003", 
    "2164711097369612", 
    "2042109031564807", 
    "2019340582208008", 
    "57c555f9e4b036ea3c50a765", 
    "5719bd5fe4b0e0971cc39ec1", 
    "5798db4ce4b021b69c548b49", 
    "572353ece4b027bcad4f2209", 
    "80d3ae848d6978531939b5fbj", 
    "2057899794380811", 
    "2147152486259203", 
    "2180154657894412", 
    "2209334500236806", 
    "2211324113126407", 
    "2208186423974414", 
    "2067650676940801", 
    "2208463566451213", 
    "2210849879014415", 
    "2211812429913613", 
    "2210186463321610", 
    "2197894428787207", 
    "2174927762547214", 
    "2213878891392015", 
    "57bd7c10e4b036ea3c3348c5", 
    "2210575422950406", 
    "20-25143886", 
    "2205149910566407", 
    "95ecb0e43dca1b56e3f6a960i", 
    "2198908611340802", 
    "5440b0e48b874a5764636bb2j", 
    "2175218875648003", 
    "2133223219046401", 
    "c974b0e459010f571bacedb0j", 
    "872db0e4b80ada57b8e0b93ci", 
    "2210624733952005", 
    "57716e7de4b0387e0f080ee2", 
    "2051165240806405", 
    "20-13009014", 
    "9066b0e4dbd2e65578c97d28i", 
    "2019445791808003", 
    "2207812104422401", 
    "8d32b0e44d16dd56edc9f039j", 
    "2207476525107208", 
    "f525b0e44b9dc7574d608d38j", 
    "575e849ee4b0b8edcd25a92e", 
    "2082210440268800", 
    "2188253975436811", 
    "576a1a40e4b0b5a18c978d96", 
    "577869b5e4b0bb9d4a8a71f2", 
    "2173509727692812", 
    "2213948416332809", 
    "966db0e46bc173578dc7a240i", 
    "2198404870617603", 
    "2207997549171202", 
    "ce1fae843c030c5468ddbe38j", 
    "2188213151347214", 
    "2028874560268814", 
    "2213794750003214", 
    "2208942769356815", 
    "2211185124774405", 
    "2100589133107207", 
    "574a9dc6e4b0f5c6d4654160", 
    "2201280352537600", 
    "2031141475635210", 
    "20-15913482", 
    "20-1822335", 
    "2199558848716815", 
    "57ac1bf6e4b036ea3bffea7f", 
    "2213946783219212", 
    "0c76b0e410961b577221c2e2j", 
    "20-22352785", 
    "2213564079142412", 
    "0872ae847a5a3a548f45aaa9j", 
    "2208898874700801", 
    "2196968311846403", 
    "2050568145932810", 
    "7143b0e4844e30577e6f0ff5i", 
    "573ef586e4b02e65380da024", 
    "2211304788160005", 
    "2031077653696010", 
    "20-6584222", 
    "2207225967923211", 
    "2210231065779208", 
    "2213762249932811", 
    "2215686890700806", 
    "2210227307136008", 
    "2212271564748811", 
    "2207397958720014", 
    "20-1085731", 
    "2093553006566405", 
    "2186019411737611", 
    "2211273055116813", 
    "2057556434073607", 
    "2015096388019211", 
    "571abe92e4b04520b1c95098", 
    "6c0bb0e4954438566f807f30i", 
    "2204900974348804", 
    "2c3dae8438222353ad2d1357j", 
    "5745b820e4b082f29d561fbd", 
    "a8aeb0e456763a57f98f0e3fj", 
    "57ddc51be4b0c59439f4f8d5", 
    "2174748432704004", 
    "429dae84e1eabd5553eb1a52j", 
    "6c2db0e492e4e456ee2797bej", 
    "57222a1ee4b00c836a3ba8a0", 
    "2208193088307205", 
    "4375b0e44167f756af8c4503j", 
    "20-23212779", 
    "57220e19e4b00c836a362875", 
    "2208982002816004", 
    "52b1b0e4ef2ad2574caca0a7j", 
    "2199633337113601", 
    "2055897931328007", 
    "2179733955494404", 
    "2049929644902414", 
    "2213416007334400", 
    "2212356066419214", 
    "2209325741324801", 
    "2062045455769609", 
    "2179297938956801", 
    "2197262278387209", 
    "573c6299e4b0ce968b4ead33", 
    "2164887738598414", 
    "57ce528de4b021b69d225db2", 
    "20-1201058", 
    "579b0e8ce4b021b69c67f0dd", 
    "2212563695462414", 
    "2201779984281601", 
    "2211205180480007", 
    "57482648e4b0bed584aa78f2", 
    "2211358267225609", 
    "2041176210406409", 
    "2186053800499210", 
    "2201818170201615", 
    "2192889309081615", 
    "2047842893120011", 
    "5764db86e4b0b8edcd503f1f", 
    "2215118129369600", 
    "2163161147008011", 
    "571adb98e4b0e0971ce42bca", 
    "2043518687987208", 
    "2181560412390407", 
    "2213598969484811", 
    "20-24430072", 
    "cc21b0e4e453c456dc2a1754j", 
    "2195996264857615", 
    "2211295339289615", 
    "575d52d5e4b0b8edcd1d7c6e", 
    "2211464256998406", 
    "bf2aae84eee65d53782b36c6j", 
    "805fb0e4c0c86f575baf251fj", 
    "20-257264", 
    "2018088882112011", 
    "2211436867827211", 
    "2210761606540802", 
    "2076186884915203", 
    "2013880218419212", 
    "2176083805952015", 
    "20-5252335", 
    "5719b3cde4b0e0971cc25389", 
    "2216024150297611", 
    "2212451325824008", 
    "2205668862336003", 
    "2214966885312005", 
    "2017734552217600", 
    "2211244752268808", 
    "2209512068364800", 
    "2181230496320012", 
    "6c0bb0e40aba5256f2cd9930i", 
    "2201316952320003", 
    "5784ed9be4b0c42066da5cdd", 
    "2198508618240014", 
    "2174479889382402", 
    "2192729564608014", 
    "2208047462374411", 
    "2208118452966405", 
    "5767fa75e4b03e8a82280352", 
    "2135361859699210", 
    "2175836904179206", 
    "2213381775078403", 
    "2212680860723211", 
    "2213984987737606", 
    "2170308727744005", 
    "57bfa3dae4b021b69cef2e13", 
    "2bfbb0e464beec56e1831d78j", 
    "2208859311641606", 
    "2189100041536012", 
    "2190566761753612", 
    "2175705265011207", 
    "2210685634969606", 
    "2081388321024000", 
    "c81bae846b315254207a32abj", 
    "2065273250483212", 
    "57234eece4b0a64f19f217b7", 
    "2170871633753614", 
    "2216260924416008", 
    "20-2184429", 
    "2086520392512000", 
    "2077338834508813", 
    "0c76b0e4726b18571dcec1e2j", 
    "2210276687782401", 
    "2211620935168011", 
    "2073452280947208", 
    "2205013925555204", 
    "57c6ff38e4b036ea3c5d29f4", 
    "20-20978697", 
    "5768b588e4b0b8edcd70ab01", 
    "20-23079692", 
    "2156366639552008", 
    "2072430246681615", 
    "2058686247756807", 
    "5a31b0e48c522457251a7c3bj", 
    "571a16c7e4b04520b1b7f1c3", 
    "2200213737292801", 
    "2216871971673615", 
    "2190214721702405", 
    "2057538485350401", 
    "2054198774489607", 
    "2194143466444804", 
    "2211390709632005", 
    "6ad6b0e4c4d7c7575d4606c8j", 
    "2158130130150412", 
    "2216688853644805", 
    "d01fae84d8d04b56d161bab6j", 
    "2209335196633610", 
    "23d2ae8404f51456f22a9b0cj", 
    "2098412141209602", 
    "07eeb0e4891fd9563a63131cj", 
    "2210586948505614", 
    "2178213757747202", 
    "2205765856640007", 
    "2212246069171208", 
    "2211735054796807", 
    "2193541086348815", 
    "2127523152243207", 
    "2216132230515206", 
    "1527b0e4e7544d5733627635i", 
    "368bb0e478294e5773be760bj", 
    "fcadae84aee729563b17c90dj", 
    "2069589519270401", 
    "2213838341465607", 
    "2084427117696010", 
    "2173711540518400", 
    "2213972117465606", 
    "2209302894899211", 
    "7143b0e4a6915557edf023f5i", 
    "577b6dfae4b0bb9d4a954cde", 
    "578b2cd7e4b021b69c1ddc38", 
    "2082991461798402", 
    "2188746725235203", 
    "2216882303577600", 
    "20-9668900", 
    "2214018984934412", 
    "2209009351974402", 
    "2198565695475213", 
    "af3eb0e481e6e756ee1d8a92j", 
    "2208355002816010", 
    "20-7519087", 
    "2057908757030403", 
    "2216972705766401", 
    "f409b0e4673afa56dc4dfad1i", 
    "2217029734118407", 
    "11-122321532", 
    "2207922118643210", 
    "2184032521689602", 
    "2217109169817614", 
    "6c0bb0e4c3784e562dd29530i", 
    "de47ae8457b985534e58c859j", 
    "2058639790028803", 
    "2166062842316804", 
    "47adae84d12dfc530412ce9aj", 
    "2215905384460813", 
    "2215573344691202", 
    "2217209556108813", 
    "1e48b0e4a0ffd9578a9c2e5fi", 
    "2162043180812803", 
    "2198173101734409", 
    "20-24159493", 
    "966db0e4a406a0577853bd40i", 
    "2210366200371200", 
    "57d503c2e4b036ea3c8b602f", 
    "2085015194035210", 
    "2202094348902412", 
    "c9faae84034d26536aa27c8dj", 
    "2204965858790400", 
    "57288342e4b027bcad6b3ee8", 
    "2082881282112013", 
    "2195705496140803", 
    "2157315111680000", 
    "2180497142592010", 
    "2189065970188803", 
    "04ed10a3d184fe501aa267faj", 
    "20-15365504", 
    "7d52b0e4865c835754ac2095j", 
    "2218214056345610", 
    "571ae0e0e4b0e0971ce51ca7", 
    "5e1aae84a2b0e953c4904d87j", 
    "20-9985184", 
    "2181823445670412", 
    "53f821df0cf2c170fa4a4db4z", 
    "57223c5be4b0bc5bc4a4f339", 
    "2095317273587214", 
    "2217145299161601", 
    "2106383939968004", 
    "2212463279910411", 
    "ffa0b0e44323e656b5e441bbi", 
    "2209060375180800", 
    "2145406703846402", 
    "2214773070412815", 
    "576b7c70e4b0b1874c449ab9", 
    "2214505627161607", 
    "2212658847116815", 
    "2214476168588806", 
    "2218281705856013", 
    "575810f1e4b07aeffd42f56c", 
    "13-862796", 
    "2213490487910404", 
    "2212402813478403", 
    "2196663520844801", 
    "2179811902540807", 
    "22bab0e46bce8c56bb453947j", 
    "2212574932492812", 
    "2211470643942406", 
    "d3b3ae84d8944856f95d806cj", 
    "2217784674598413", 
    "2205756181798406", 
    "2211278499712005", 
    "5762a473e4b03e8a82046090", 
    "579178e7e4b021b69c3b2df7", 
    "2214982608268815", 
    "5033ae8475570655c7ae4518j", 
    "2213079756326408", 
    "6fdcb0e4e2bff256c01519bcj", 
    "2218024876953600", 
    "6c0bb0e42bb93456b18e7b30i", 
    "20-21768204", 
    "872db0e416decc57b871b43ci", 
    "5718e7e9e4b011ad83669956", 
    "2187448736729615", 
    "1794ae84c2d53256116c0ed7j", 
    "ffa0b0e44feecb56e50e2dbbi", 
    "2211457043276815", 
    "2211391165529600", 
    "2032628668019204", 
    "2187408502937614", 
    "2218014091571206", 
    "571a64fee4b0e0971cda976b", 
    "2188548667251205", 
    "2055793589171215", 
    "2216893724480002", 
    "20-13706730", 
    "2211684926016010", 
    "2205901515648003", 
    "57752bdce4b056b7a982ef95", 
    "2113022275699212", 
    "2210310943846414", 
    "2217977559795209", 
    "2218095847500813", 
    "2201790225561601", 
    "2075170163507205", 
    "2209136010150400", 
    "2209396347200010", 
    "a899b0e44c456656c29cacdai", 
    "2210195065600009", 
    "2207758717708813", 
    "5786e936e4b0e7f82b19ca65", 
    "13-595065", 
    "2167568381632011", 
    "2195986109222405", 
    "2137484374809609", 
    "2063278775436801", 
    "57627ac3e4b03e8a81fec6bd", 
    "2203621064358411", 
    "2207568933094403", 
    "2035486949427212", 
    "2216945392896012", 
    "2203768053836800", 
    "2207342874393610", 
    "2088046645171207", 
    "2210095034265603", 
    "0f70b0e4ca7fb9573445630ej", 
    "5723e70de4b027bcad694fd5", 
    "6c73b0e4d779e35728015cf6j", 
    "966db0e4019478570c6ea640i", 
    "8226b0e42930b355b23001a9i", 
    "2213519384832011", 
    "7d52b0e40b238b5779bc2195j", 
    "11-122702374", 
    "2092277736192012", 
    "2210319427891207", 
    "57ce72bce4b036ea3c7343c0", 
    "57711bfce4b0ad9716f6b52d", 
    "2212593834035200", 
    "2173002615705601", 
    "5719ef33e4b04520b1b3a653", 
    "2210698315251203", 
    "2217895586752006", 
    "2168584648435201", 
    "2213518253772808", 
    "df9bb0e482142d57cbc5fdf3j", 
    "aaf0b0e43d9e5b5771ba2c17j", 
    "2188031710950401", 
    "2183586380979207", 
    "2197233989286411", 
    "57196b41e4b011ad837d1dca", 
    "20-12372008", 
    "2178070692032015", 
    "2199537348300807", 
    "29f3b0e43ded6f57ef5c4630j", 
    "2205753850880005", 
    "2197295592550410", 
    "2216193744819203", 
    "20-8057361", 
    "2099712155891206", 
    "2116024190924813", 
    "13-726933", 
    "20-25346146", 
    "57a1f3d1e4b036ea3bd86fc7", 
    "2118424165964801", 
    "571ac16ee4b0e0971cdf7ee2", 
    "d423b0e47834bf56aa418159i", 
    "2178072487641612", 
    "2073285782758415", 
    "2188274703987202", 
    "20-24361580", 
    "577e8303e4b0c42066c45dd8", 
    "2206930770777604", 
    "57512c32e4b01a49a0e33c7b", 
    "2189663498598403", 
    "2186367937216000", 
    "11-122172427", 
    "571a566fe4b04520b1c28992", 
    "fcfeae84d9d5b7521a44010ej", 
    "2193498284006405", 
    "2219142906854408", 
    "2217003286963213", 
    "2199731383155212", 
    "2215549235059214", 
    "2217971146854400", 
    "2214021712102412", 
    "2211232709094413", 
    "20-4528989", 
    "5723e7b0e4b0a64f1a0d0940", 
    "2164938540646408", 
    "c3d2ae8408adda55a80fb650j", 
    "2188178221734410", 
    "2050996630361612", 
    "2181384644326411", 
    "5718ef51e4b011ad8367c65c", 
    "20-24149730", 
    "37afb0e448c1ff5627e428bcj", 
    "1794ae84ce9a4c56d06e2bd7j", 
    "872db0e496bad457b8eeb73ci", 
    "2050223400371202", 
    "2161863811712011", 
    "2176974316684804", 
    "20-15101950", 
    "2066405449868815", 
    "2056399506828815", 
    "2219431776985609", 
    "20-25516040", 
    "2207930817523215", 
    "2211360678284806", 
    "20-13828707", 
    "1527b0e454a13e57978e6e35i", 
    "20-20062515", 
    "2176141842188811", 
    "2219538432601607", 
    "2157479090188802", 
    "2051080572979204", 
    "2120449207577600", 
    "571974f2e4b03f53f1c334b4", 
    "20-17387338", 
    "2133253288678408", 
    "2213668914240003", 
    "20-17211921", 
    "20-11260012", 
    "d423b0e43738de566c6b9c59i", 
    "2217877534924814", 
    "5719dcbbe4b0e0971cc7bde3", 
    "2170690638707211", 
    "2216950264409603", 
    "d423b0e427e8b556588c7f59i", 
    "2175756345152002", 
    "2218919507276801", 
    "2046908306470410", 
    "2211575941862402", 
    "6c0bb0e402f5255685426e30i", 
    "2161723906444802", 
    "48e4b0e4a7243c5795c390ddj", 
    "2218360320089615", 
    "2213860168499202", 
    "2211313908339211", 
    "2097949797555201", 
    "2029861831769613", 
    "57230a3fe4b027bcad3ffcbc", 
    "2119878903577608", 
    "2095286279897603", 
    "2193413829900803", 
    "2179358726425603", 
    "2211714228364809", 
    "2219267591065607", 
    "2212559967641606", 
    "572335dbe4b027bcad49ab54", 
    "2056384438579200", 
    "2210342623385612", 
    "2220066051584002", 
    "20-4225222", 
    "2187134661670413", 
    "2201847157504004", 
    "2185721612659210", 
    "20-17724603", 
    "2182479169216014", 
    "5780bae6e4b0e7f82b060514", 
    "2199479611456010", 
    "2220206540224007", 
    "57ac2c60e4b021b69cb0946f", 
    "ed23ae841660275699e515b9j", 
    "ba9bae84965f2f56ba7b78dfj", 
    "2176883254310410", 
    "fcb8b0e4abdbe056b453bfe9j", 
    "20-4030195", 
    "2217837917900811", 
    "2191308117875215", 
    "2185690135334401", 
    "2217885362240012", 
    "2049693717452809", 
    "2020880840921614", 
    "2f222e71b024925163801fc8j", 
    "2172620220454412", 
    "57c6dee5e4b036ea3c5956ed", 
    "2055268964096013", 
    "2189489116096013", 
    "2220458760704014", 
    "20-18031166", 
    "20-14964016", 
    "2212538191385608", 
    "1ca5b0e41ccc52573e856d66j", 
    "2109472330764815", 
    "576919d4e4b0cb9a548934e1", 
    "debab0e497ffab572f044edfi", 
    "20-25373771", 
    "2213445401062402", 
    "966db0e40d827f571cfdab40i", 
    "13-258980", 
    "2220403232025601", 
    "2192996396377608", 
    "577b57bae4b0bb9d4a9487ff", 
    "2220772629222405", 
    "2199345883635208", 
    "2202459350848013", 
    "2213714879385601", 
    "2159885933132802", 
    "2213370950016014", 
    "2213630022771204", 
    "cb7eb0e4fdf765573d52dab8j", 
    "57223bd6e4b0bc5bc4a4b1a9", 
    "2188150587507203", 
    "6c73b0e453c3d757ced85af6j", 
    "2217302295641611", 
    "2213895744025603", 
    "2014871743872003", 
    "2185835827584013", 
    "2197196566438405", 
    "20-11444534", 
    "2185722864563213", 
    "2212354913766400", 
    "2221163273843214", 
    "578ee105e4b021b69c2ef38e", 
    "2073646409689613", 
    "20-12237188", 
    "2079820736460814", 
    "2221201389516813", 
    "2221263333772808", 
    "f409b0e492fd05572ecc03d2i", 
    "20-21339926", 
    "106740461", 
    "20-15032766", 
    "20-10872100", 
    "2020169431270405", 
    "07eeb0e40b07d8568e1a131cj", 
    "2200196571904013", 
    "55d57b4d84ae85fe6199e8acz", 
    "20-24553879", 
    "571a1ea0e4b04520b1b90c37", 
    "8d32b0e46cbed7565a60ef39j", 
    "6c0bb0e439d9fa554b7a4830i", 
    "2015685179571204", 
    "2104074636723206", 
    "2229030904665609", 
    "2231360690713603", 
    "2228253707852807", 
    "2048631630963210", 
    "2220993058355215", 
    "2208781043814404", 
    "2225673147852812", 
    "2128547621990415", 
    "2199282662720010", 
    "2203424000268800", 
    "2185227820761615", 
    "2825b0e408651057b50175fdi", 
    "2219198420403214", 
    "2210318947737611", 
    "2208764007718411", 
    "2213151234329603", 
    "2213366109785612", 
    "5747cba3e4b0bed584a983bd", 
    "2227929124774400", 
    "2fe6ae8424b59a528d23f716j", 
    "2181381682214406", 
    "2227322655129611", 
    "2065382966528009", 
    "2047287234060806", 
    "2211319408486406", 
    "91698592", 
    "2137293007795203", 
    "2168775060710404", 
    "2825b0e4ee9d1957bc8e79fdi", 
    "57232d07e4b027bcad47b068", 
    "573d2c8ee4b0a432bfb70dd2", 
    "571adfa8e4b04520b1cf28d9", 
    "2225218669132807", 
    "2228633565440013", 
    "2095193959974406", 
    "2228635314329603", 
    "2228634004889607", 
    "5774482de4b0387e0f1bb291", 
    "2207347769779200", 
    "2194091453260803", 
    "2030442822272009", 
    "2184016214400004", 
    "20-12656306", 
    "2232875012889605", 
    "2196650059609608", 
    "2196418974694411", 
    "2218713960588810", 
    "2220061049792013", 
    "2033298134899207", 
    "2232783231027204", 
    "57b16158e4b036ea3c1022fd", 
    "2078625161600012", 
    "2185222137574410", 
    "2164882548710411", 
    "2051431728102405", 
    "2102011172620800", 
    "2206362677440014", 
    "571ab3f9e4b0e0971cdd4b89", 
    "57bce87fe4b021b69ce14533", 
    "2228635551257612", 
    "5783829ce4b0e7f82b0a7f43", 
    "5723db89e4b027bcad6743b7", 
    "2222638545638404", 
    "2233259491392012", 
    "2164366438284807", 
    "5749aae2e4b0f5c6d4643a8a", 
    "20-25462306", 
    "2232406409228801", 
    "2223120341772801", 
    "2226239945382411", 
    "2178602571392010", 
    "574d44aae4b083a06e25dd22", 
    "57235252e4b0a64f19f2a1ec", 
    "2210683576230413", 
    "5719c170e4b04520b1ae7074", 
    "5719e2ffe4b04520b1b2daca", 
    "2232503409561610", 
    "2029070854259206", 
    "57ce9258e4b036ea3c742418", 
    "57c5fec8e4b036ea3c536fb3", 
    "576a2479e4b0b5a18c98191a", 
    "2188905509094413", 
    "2232784594419209", 
    "2166538542323200", 
    "2212365025702410", 
    "2234496299264005", 
    "2194097622656004", 
    "571a5836e4b04520b1c2f14e", 
    "2231857293824006", 
    "2228629014566413", 
    "f409b0e4dffd165791150ed2i", 
    "2046566207641606", 
    "2227266482035215", 
    "2226015416998400", 
    "2066589747942413", 
    "2185733283545605", 
    "11-123420210", 
    "2221465536832001", 
    "2207869656793601", 
    "20-22902178", 
    "2166522588441602", 
    "5724a67ee4b0a64f1a0d961e", 
    "57230e59e4b0a64f19e46f92", 
    "57239517e4b0a64f19fedff3", 
    "578d8979e4b036ea3b777b66", 
    "578a368ce4b036ea3b6bbed9", 
    "2221834653132803", 
    "2232867762854400", 
    "2140899033689615", 
    "2231596616768014", 
    "0f70b0e40cd9d757b705660ej", 
    "2170957497651201", 
    "2232880847142400", 
    "20-14778989", 
    "57238209e4b027bcad56a64d", 
    "577c8a10e4b0bb9d4a9b8568", 
    "2195997830937605", 
    "2048487482444800", 
    "2228641481036815", 
    "57678bf6e4b03e8a82156db4", 
    "2228627915724813", 
    "578ee329e4b036ea3b7ec6b1", 
    "2228627361036808", 
    "2191892169561603", 
    "5723db8be4b0a64f1a0adb7a", 
    "2228870057561611", 
    "571a658fe4b04520b1c4fd38", 
    "2172149026572813", 
    "33dcae84785dd753ad546127j", 
    "57195d6be4b03f53f1bf204d", 
    "2232877785472006", 
    "2227520965478405", 
    "2215448653222415", 
    "2232789896268815", 
    "2232788310387208", 
    "2232786932032005", 
    "2227619090150406", 
    "2163192430745609", 
    "57239e3ae4b027bcad5d530c", 
    "2235359142835204", 
    "2235272027814411", 
    "2235270662156812", 
    "5749796ae4b074699ebc3592", 
    "2235268832908810", 
    "575e8411e4b03e8a81e1a1fa", 
    "2235267007846403", 
    "2045712458918404", 
    "57df8324e4b082bdd0c129aa", 
    "571959b2e4b03f53f1be695c", 
    "2234996054080005", 
    "2164497354470404", 
    "2181194251840015", 
    "2047982957696001", 
    "2053247819520004", 
    "6356ae84d4d24954e5dfcf77j", 
    "2198860548812814", 
    "95ecb0e45351305630efbb60i", 
    "2235367733004803", 
    "57917688e4b021b69c3b0f02", 
    "2235366671142403", 
    "2235358826240008", 
    "8cb8b0e47a7667576be0ce02i", 
    "2221903007923210", 
    "2235280980902414", 
    "5762a00ce4b0b8edcd47c1de", 
    "2051037064000014", 
    "57238f4fe4b027bcad59f46a", 
    "2235266797299207", 
    "2235265586240001", 
    "2066408515852801", 
    "57e395f0e4b082bdd0e213bd", 
    "2071036948544006", 
    "574ff1bae4b0cdd132b889e6", 
    "57230858e4b0a64f19e315d5", 
    "2175448059097603", 
    "572382b5e4b0a64f19fa563c", 
    "572d3c27e4b05cbfcd699266", 
    "5750d5e4e4b06d1012d89ea5", 
    "2179165338342407", 
    "57d02280e4b021b69d2c30f7", 
    "2211970148633613", 
    "ffa0b0e4af1cdd5630bd3cbbi", 
    "2210329084236815", 
    "2226985924505613", 
    "2186845242009609", 
    "7143b0e424523357a34811f5i", 
    "f409b0e457560b57009807d2i", 
    "2825b0e4d2a01c57b7f47afdi", 
    "872db0e4e7d7d357afbab73ci", 
    "2231855859545605", 
    "ffa0b0e4abb5e8566e7243bbi", 
    "2171439527833613", 
    "2227431781760007", 
    "95ecb0e40d32f955eab28b60i", 
    "2233909621824014", 
    "558db0e4a9e67857729ca8abi", 
    "57c4f8cfe4b036ea3c4f5c0a", 
    "2231853486707201", 
    "2211023546329613", 
    "57191fabe4b03f53f1b3f443", 
    "2044248171366413", 
    "572328c6e4b0a64f19ea5a70", 
    "2229002892505605", 
    "2230583295078400", 
    "2038806637619201", 
    "6c73b0e42f9cbf57f19658f6j", 
    "2179050378457602", 
    "2221059249164800", 
    "2210494771584011", 
    "2212889757260807", 
    "2187535152012808", 
    "2165231313766411", 
    "2227797328832008", 
    "574302a4e4b0327ae6bcfdbb", 
    "2228628698598402", 
    "2228628489856005", 
    "2181188133708814", 
    "2033218981721611", 
    "2235364210521609", 
    "2213056373004811", 
    "e535b0e4434c7d56ffd431bai", 
    "57d2c8a3e4b021b69d3876ba", 
    "84b7ae848047f751a0719d18j", 
    "4156b0e4b77587570fe60f5fj", 
    "2029381261747204", 
    "2235278246656012", 
    "2202904626841602", 
    "57cedc13e4b021b69d261c7c", 
    "2073082130060813", 
    "2163138147366412", 
    "2219278331417610", 
    "5773b209e4b0ad97170864ba", 
    "20-8106922", 
    "5719222fe4b03f53f1b47231", 
    "cb7eb0e4aad36357ef1adab8j", 
    "2204018631283204", 
    "5719184ce4b03f53f1b29b74", 
    "2052179210355204", 
    "2200437516633609", 
    "2235365719360009", 
    "2235359983654405", 
    "57bef9afe4b036ea3c3b5949", 
    "2235353311424006", 
    "2091078252352008", 
    "2097300021990414", 
    "2235284337267204", 
    "5743a89fe4b02e653813d338", 
    "2086468579980805", 
    "2235269490201611", 
    "2175476547328011", 
    "2235267754342415", 
    "2235267562368005", 
    "2235261267712010", 
    "20-24138757", 
    "2215273849433600", 
    "2228628756057613", 
    "2089883212940807", 
    "57a5759fe4b036ea3be67d37", 
    "572215dfe4b00c836a381a57", 
    "571a278ce4b0e0971cd00fb9", 
    "57dbe0b8e4b0c59439e629c2", 
    "57dbdad2e4b0c59439e17200", 
    "ffa0b0e447c2d35602e634bbi", 
    "2177558704102403", 
    "2082997570752008", 
    "2177494654694407", 
    "2235099100236808", 
    "2235096516403213", 
    "2073020646387211", 
    "5723b933e4b0a64f1a040c8d", 
    "b3efae848253b0551c46f208j", 
    "5719ad9de4b04520b1abcb17", 
    "5758bc9de4b00e8144002bf7", 
    "576b9cb6e4b0b1874c468151", 
    "2235007192486404", 
    "57194e49e4b03f53f1bc591f", 
    "57df6ecfe4b082bdd0c0c374", 
    "2219610813171200", 
    "2228627749964813", 
    "2017303802918408", 
    "1527b0e4e1874e571c2c7735i", 
    "2087668217894409", 
    "2173423158361604", 
    "2090729381849608", 
    "57239167e4b0a64f19fdf588", 
    "2080338041907201", 
    "2224956995276809", 
    "571b1d81e4b0e0971cedd48c", 
    "2188650237657600", 
    "2174306242483207", 
    "2211308815334414", 
    "2208369562316804", 
    "2231861322790409", 
    "571a669ce4b0e0971cdae6b0", 
    "5723e7b2e4b0a64f1a0d0986", 
    "57192acce4b03f53f1b605d5", 
    "57a4210ee4b021b69c8ee3b2", 
    "2135175394073611", 
    "5723212fe4b027bcad454867", 
    "2191021588377605", 
    "2232409770176003", 
    "2164403030028804", 
    "2176907938777614", 
    "2223304321638415", 
    "2231901715904015", 
    "2020090938393606", 
    "2213447909465611", 
    "b7e6b0e49760845737c6bf85j", 
    "2233450338368001", 
    "20-3843463", 
    "2178555881292805", 
    "2231598193344014", 
    "2220006202329610", 
    "2203548213273600", 
    "571960a2e4b03f53f1bfb5f4", 
    "2206426490880012", 
    "2016716780057604", 
    "575ea64ee4b0b8edcd27b933", 
    "57ad4342e4b036ea3c049d7a", 
    "2233906578393602", 
    "2228628589286412", 
    "2233891781081608", 
    "57234e61e4b0a64f19f1fd2a", 
    "574d41e1e4b0740bcb7ee5a4", 
    "2165448514048005", 
    "2189761903987212", 
    "57c30b38e4b036ea3c461b7a", 
    "2232866732006403", 
    "574d6c1ce4b0740bcb82d805", 
    "2188649238771202", 
    "2206353849881604", 
    "2195833301888009", 
    "2184134201881615", 
    "2174350252940804", 
    "5718e6a3e4b03f53f1aacbf9", 
    "57235194e4b027bcad4ef02b", 
    "5719490be4b03f53f1bb6e88", 
    "57230cb1e4b0a64f19e42ba2", 
    "578860b0e4b036ea3b6675f1", 
    "571a116ae4b04520b1b72d9c", 
    "57232cd0e4b027bcad479f1f", 
    "2231673509324803", 
    "574585e6e4b05779da279b13", 
    "5723e211e4b027bcad68882b", 
    "571b1b74e4b0e0971ced5f84", 
    "2104402079116805", 
    "41a3b0e472bf8557116e1bc7j", 
    "d423b0e4cddccb566ade8b59i", 
    "2230604832460809", 
    "20-22115847", 
    "2230580794777603", 
    "57194869e4b03f53f1bb56b6", 
    "571adf00e4b04520b1cf1131", 
    "2182187198323203", 
    "2042126593356808", 
    "2227885757017613", 
    "57ab26efe4b036ea3bf9f135", 
    "2230595390988802", 
    "2114459203366411", 
    "2206417795916814", 
    "571a644fe4b04520b1c4cb47", 
    "57bcb8d5e4b036ea3c30687e", 
    "716fb0e4609dc45586794ea1i", 
    "3389b0e4b466de55dabca921i", 
    "20-23840395", 
    "5719cfe7e4b0e0971cc619ed", 
    "2232882544128012", 
    "2232878569113602", 
    "b5c4b0e4c64ea856e28ae65fj", 
    "5532544e84ae8c6af210cc38z", 
    "574b9f13e4b074699ec13d05", 
    "2126328645529614", 
    "2232789558400010", 
    "2232787163916805", 
    "578dac9ae4b036ea3b7930b1", 
    "2039997041740801", 
    "57dbd93de4b0c59439e033fd", 
]

logger = None
def get_logger():
    global logger
    if not logger:
        logger = logging.getLogger('')
        formatter = logging.Formatter(
            fmt="%(asctime)s %(filename)s %(threadName)s %(funcName)s [line:%(lineno)d] %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S")
        stream_handler = logging.StreamHandler()

        rotating_handler = logging.handlers.TimedRotatingFileHandler('/data/logs/morgan-spider/chiahr_check_auth.log','midnight',1)

        stream_handler.setFormatter(formatter)
        rotating_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        logger.addHandler(rotating_handler)
        logger.setLevel(logging.INFO)
    return logger

def get_device():
    a='1234567890'
    b=[random.choice(a) for i in xrange(15)]
    return ''.join(b)

def login(username, passwd, proxy, deviceid):
    logger = get_logger()
    return_result = {'login_data': '', 'session': None, 'code': 1}
    for i in range(3):
        logger.info('start login '+ str(username))
        mobile = username
        password = passwd

        headers = {
            'versionCode': 'Android_30',
            'versionName': 'Android_5.9.0',
            'UMengChannel': '2',
            'uid': '',
            'Cookie': 'bps=',
            'appSign': '-1012826753',
            'deviceID': deviceid,
            'deviceName': 'MI5S',
            'role': 'boss',
            'deviceModel': 'MI5S',
            'deviceVersion': '6.0',
            'pushVersion': '52',
            'platform': 'Android-23',
            'User-Agent': 'ChinaHrAndroid5.9.0',
            'extion': '',
            'pbi': '{"itemIndex":0,"action":"click","block":"03","time":%s,"targetPage":"b.LoginActivity\/","page":"2302","sourcePage":""}' % str(int(time.time()*1000)),
            'Brand': 'Xiaomi',
            'device_id': deviceid,
            'device_name': 'MI5S',
            'device_os': 'Android',
            'device_os_version': '6.0',
            'app_version': '5.9.0',
            'uidrole': 'boss',
            'utm_source': '2',
            'tinkerLoadedSuccess': 'false',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'passport.chinahr.com',
            'Accept-Encoding': 'gzip',
        }

        # login
        # print 'proxies is', proxy 
        logger.info('proxies is' + str(proxy))
        try:
            session = requests.session()
            response = session.post('https://passport.chinahr.com/app/login', data={
                'input': mobile,
                'pwd': password,
                'source': '0',
                'msgCode': '',
            }, headers=headers, proxies=proxy, timeout=30)
            json_data = response.json()
            logger.info('return result of login %s' % json_data)
            code = json_data.get('code')
            msg = json_data.get('msg')
            data = json_data.get('data', {})
            if code in [0, '0']:
                # cookie = dict(response.cookies)
                # login_data = data
                return_result['session'] = session
                return_result['code'] = 0
                return_result['login_data'] = data
            else:
                continue
            return return_result
        except Exception, e:
            logger.info(str(traceback.format_exc()))
            return_result = {'login_data': '', 'session': None, 'code': 2}

        logger.info(str(username) + ' login error times ' + str(i))
    return return_result

def check_download(login_result, cvid, proxy, deviceid):
    logger = get_logger()
    result = {'code': 0}
    if not login_result:
        logger.info('there has no login_result in resume, return!!!')
        result['code'] = 1
        return result
    if not proxy:
        logger.info('there has no proxy in resume, return!!!')
        result['code'] = 5
        return result
    if not cvid:
        logger.info('there has no cvid in resume, return!!!')
        result['code'] = 2
        return result
    session = login_result['session']

    try:
        check_download_headers = {
            'versionCode': 'Android_30',
            'versionName': 'Android_5.9.0',
            'UMengChannel': '2',
            'uid': str(login_result['login_data']['uid']),
            'appSign': '-1012826753',
            'deviceID': deviceid,
            'deviceName': 'MI5S',
            'role': 'boss',
            'deviceModel': 'MI5S',
            'deviceVersion': '6.0',
            'pushVersion': '52',
            'platform': 'Android-23',
            'User-Agent': 'ChinaHrAndroid5.9.0',
            'extion': '',
            'pbi': '{"itemIndex":0,"action":"click","block":"01","time":%s,"targetPage":"b.ResumeDetailActivity\/","page":"2501","sourcePage":""}' % str(int(time.time()*1000)),
            'Brand': 'Xiaomi',
            'device_id': deviceid,
            'device_name': 'MI5S',
            'device_os': 'Android',
            'device_os_version': '6.0',
            'app_version': '5.9.0',
            'uidrole': 'boss',
            'utm_source': '2',
            'tinkerLoadedSuccess': 'false',
            'Host': 'app.chinahr.com',
            'Accept-Encoding': 'gzip',
        }

        # need to renzheng
        check_download_url = 'https://app.chinahr.com/cvapp/checkDownload?cvid=%s' % cvid
        response = session.get(check_download_url, headers=check_download_headers, proxies=proxy, timeout=30)
        json_data = response.json()
        result['data'] = json_data
        if json_data.get('code', -1) not in [0, '0']:
            logger.info('get error result of check_download_url!!!'+str(json_data))
            result['code'] = 6
            return result
        # print response.text
        logger.info(response.text)
    except Exception, e:
        logger.info('unkown error'+str(traceback.format_exc()))
        result['code']=4
    return result

def check_thread(proxy):
    logger = get_logger()
    logger.info('check thread start.')
    # proxy = {'http': 'http://H01T3Z8ZSM11D61D:154F545DD00DA6B3@proxy.abuyun.com:9020', 'https': 'http://H01T3Z8ZSM11D61D:154F545DD00DA6B3@proxy.abuyun.com:9020'}
    start_count = 41316
    f=open('need_check', 'r')
    account = None
    result = open('result', 'a')

    save_count = 30

    while True:
        while start_count:
            account = json.loads(f.readline())
            start_count -= 1
        time.sleep(1)
        account = json.loads(f.readline())
        deviceid = get_device()
        if not account:
            break
        logger.info('deal with:'+str(account))
        login_result = login(account['encode_mobile'], account['encode_pwd'], random.choice(proxy), deviceid)
        if login_result['code']:
            account['status'] = 1
            result.write(json.dumps(account)+'\n')
            continue

        check_result = check_download(login_result, random.choice(cvids), random.choice(proxy), deviceid)
        if check_result['code']:
            account['status'] = 2
            result.write(json.dumps(account)+'\n')
        else:
            account['status'] = 3
            result.write(json.dumps(account)+'\n')
        if not save_count:
            save_count =30
            result.close()
            result = open('result', 'a')
        else:
            save_count -= 1
    result.close()

if __name__ == '__main__':
    logger = get_logger()
    logger.info('='*50 + '\nstart main.')

    # get_accounts_thread_one = threading.Thread(target=get_accounts_thread, name='Get_Account_Thread')
    # get_accounts_thread_one.start()

    proxies = [
    {'http': 'http://H01T3Z8ZSM11D61D:154F545DD00DA6B3@proxy.abuyun.com:9020', 'https': 'http://H01T3Z8ZSM11D61D:154F545DD00DA6B3@proxy.abuyun.com:9020'},
    {'http': 'http://H2CI114ZXVK7355D:C889D07037AA2C14@proxy.abuyun.com:9020', 'https': 'http://H2CI114ZXVK7355D:C889D07037AA2C14@proxy.abuyun.com:9020'}
    ]
    check_thread(proxies)

    # check_thread_list = []
    # for i in xrange(6):
    # # for i in xrange(settings.DOWNLOAD_THREAD_NUMBER):
    #     check_thread_one = threading.Thread(target=check_thread, name='Thread-'+str(i), args=(proxies[i % 2], ))
    #     check_thread_one.start()
    #     check_thread_list.append(check_thread_one)


    # for i in check_thread_list:
    #     i.join()

    # get_accounts_thread_one.join()
    logger.info('done.')

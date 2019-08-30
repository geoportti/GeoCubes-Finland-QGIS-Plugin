<img src="https://github.com/geoportti/Logos/blob/master/geoportti_logo_300px.png">

# GeoCubes Finland - QGIS plugin
A QGIS plugin to access raster data on GeoCubes Finland, maintained by Finnish Geospatial Research Institute (FGI).

[Esittely suomeksi alla](https://github.com/geoportti/GeoCubes-Finland-QGIS-Plugin#mik%C3%A4-on-geocubes-finland)

## What is GeoCubes Finland?
GeoCubes Finland is a harmonised, multi-resolution raster geodata repository. The repository contains several key national datasets on themes such as elevation, land cover and forestry. Read more: [GeoCubes Finland main site](http://86.50.168.160/geocubes) and [description on usage and citing](https://github.com/geoportti/GeoCubes).
#### Harmonised? What does that mean?
Simply that the data is as simple to access and use as can be. All of the data is in the same CRS (EPSG:3067), is georeferenced uniformly and is available as both a GeoTIFF image or a [VRT virtual file](https://gdal.org/drivers/raster/vrt.html). The data is available in resolutions ranging from 1 to 1000 meters and can be cropped flexibly with e.g. a bounding box or administrative area boundaries. Read more [here](http://86.50.168.160/geocubes/description/).
All of this means that **accessing raster datasets is easier than ever before**.
#### Who's the service for and who can use it?
GeoCubes Finland has been created under the [oGIIR project](http://ogiir.fi/) and as such, is aimed to support the needs of Finnish research community. However, the service and its data is freely usable by anyone interested.

## GeoCubes Finland plugin
This QGIS 3.x plugin enables using all of the abovementioned features effortlessly in your QGIS 3 installation. Simply select three parameters: raster layers to download, cropping method and raster resolution. Crop with a bounding box, administrative areas or draw a polygon to crop with. Then select either GeoTIFF or VRT file. After download, a layer is added to QGIS, where you can use it for further analysis. You may use files from the GeoCubes Finland server or save files to local storage: the former suits quick analysis on smaller rasters and the latter is beneficial for larger files.
#### Plugin installation
- Download the plugin to your computer from *Clone or download* -> *Download ZIP*
- Open QGIS, click *Plugins* drop-down menu and select *Manage and install plugins*
- Select *Install from ZIP* in the plugin manager. Navigate to the zip file.
#### I found a bug and/or want to suggest a new feature. What do I do now?
We are grateful for all feedback. If you find errors or have suggestions to improve the plugin, please open an issue in the repository or see infobox on top of *geocubes_plugin.py* for email information.
#### Adding layers directly to QGIS doesn't work. How to fix this?
On some envinroments, attempting to add GeoCubes layers to QGIS will always fail. One known reason for this is a GDAL driver called [DODS](https://gdal.org/drivers/raster/dods.html). Disabling this driver will fix the problem. [See here for details](https://trac.osgeo.org/gdal/ticket/6682). The easiest way to disable it is via QGIS settings. **Select Settings -> Options -> GDAL. Scroll the list and you should find a driver named DODS. Deselect it and click Ok.** You may do the same via terminals as well. Type the command GDAL_SKIP=DODS preceded by either SET or EXPORT depending on the platform. Read more on configuration options [here](https://trac.osgeo.org/gdal/wiki/ConfigOptions). 

If this didn't fix the problem, see above what to do in case of a bug. The problem can also be circumvented by only saving layers to disk.

## Citing
When using GeoCubes Finland, please cite the oGIIR project: "We made use of geospatial data/instructions/computing resources provided by the Open Geospatial Information Infrastructure for Research (oGIIR, urn:nbn:fi:research-infras-2016072513) funded by the Academy of Finland."

**Authored by [Tatu Leppämäki](https://twitter.com/tadusk0) and the Department of Geoinformatics and Cartography at FGI**

## Mikä on GeoCubes Finland?
GeoCubes Finland on Paikkatietokeskus FGI:n ylläpitämä harmonisoidun moniresoluutioisen rasterigeodatan tietovarasto. Se sisältää keskeisiä kansallisia aineistoja liittyen esimerkiksi korkeusmalliin, maanpeitteeseen ja metsätalouteen. Lisätietoa englanniksi [GeoCubes Finlandin pääsivulta](http://86.50.168.160/geocubes) sekä [käytön ja siteeraamisen kuvauksesta](https://github.com/geoportti/GeoCubes).
#### Harmonisoitu? Mitäs se tarkoittaa?
Että data on mahdollisimman helppoa saavuttaa ja käyttää. Kaikki aineistot ovat samassa koordinaattijärjestelmässä (EPSG:3067), yhtenäisesti georeferöityjä ja ovat saatavilla samoissa tiedostomuodoissa (GeoTIFF ja [Virtuaalinen tiedosto VRT](https://gdal.org/drivers/raster/vrt.html)). Moniresoluutioisuus tarkoittaa, että aineistot ovat saatavilla 1–1000 metrin resoluutioilla – rastereita voi myös rajata joustavasti mm. rajaavalla suorakaiteella tai hallinnollisten alueiden rajoilla. Tarkempi [kuvaus englanniksi](http://86.50.168.160/geocubes/description/).
Edellämainittu tarkoittaa, että **rasteridata on helpommin saatavilla ja käytettävissä kuin kuunaan**.
#### Kenelle palvelu on suunnattu?
GeoCubes Finland on kehitetty osana [oGIIR-hanketta](http://ogiir.fi/) ja siten suunnattu suomalaisen tutkijayhteisön tarpeisiin. Palvelu ja sen data ovat kuitenkin avoimesti käytettävissä.

## GeoCubes Finland QGIS-laajennus
Tällä QGIS 3.x -laajennuksella edellämainittujen ominaisuuksien käyttö sujuu vaivatta. Käyttäjän tarvitsee valita kolme keskeistä parametriä: ladattavat tasot, rajaus ja rasteriresoluutio. Rajauksen voi tehdä suorakulmiolla (*bounding box*), hallinnollisilla alueilla tai piirtää mieleisensä polygonin. Tiedostomuodoksi voi valita joko GeoTIFF- tai VRT-tiedoston. Taso lisätään latauksen jälkeen QGIS:iin jatkoanalyysiä varten. Tiedostoja voi käyttää joko GeoCubesin palvelimilta tai tallentaa paikallisesti: ensimmäinen soveltuu pienempien tiedostojen nopeisiin analyyseihin ja jälkimmäinen on hyödyllinen suuremmissa tiedostoko'oissa.
#### Laajennuksen asentaminen
- Lataa laajennus zip-tiedostona repositorion yläkulmasta kohdasta *Clone or download* -> *Download ZIP*
- Avaa QGIS 3 -versiosi, klikkaa *Plugins*-valikko ja valitse *Manage and install plugins*
- Valitse vasemmalta *Install from ZIP* ja etsi äsken ladattu tiedosto
#### Löysin bugin ja/tai tahdon ehdottaa uutta ominaisuutta. Mitä teen?
Vastaanotamme palautetta hyvin mielellään. Jos löydät virheitä tai sinulla on kehitysehdotuksia, avaa keskustelu repositorion *Issues*-välilehdellä tai ota yhteyttä sähköpostitse *geocubes-plugin.py*-tiedoston yläosan laatikosta löytyvään osoitteeseen.
#### Tasoja ei toisinaan voi lisätä QGIS:iin. Mitä teen?
Joissain ympäristöissä tason lisääminen suoraan QGIS:iin epäonnistuu aina. Eräs tunnettu syy tälle on GDAL-ajuri nimeltään [DODS](https://gdal.org/drivers/raster/dods.html). Ajurin poistaminen käytöstä korjaa ongelman. [Lisätietoja täältä](https://trac.osgeo.org/gdal/ticket/6682). Helpoiten ajurin saa pois käytöstä QGIS:n asetusten kautta. **Valitse Settings -> Options -> GDAL. Selaa listaa DODS:n kohdalle, klikkaa pois käytöstä ja paina Ok.** Saman voi tehdä terminaalin kautta: käyttäjän tulee kirjoittaa oikeaan terminaaliin käsky GDAL_SKIP=DODS jota edeltää joko SET tai EXPORT alustasta riippuen. Lue [GDAL:n asetusten määrittämisestä](https://trac.osgeo.org/gdal/wiki/ConfigOptions).

Jos ongelma jatkuu, katso ylhäältä toimet bugeja kohdatessa. Ongelman voi myös sivuuttaa lataamalla tasot aina kovalevylle.

## Viittausohjeet
Jos käytät GeoCubes Finlandia työssäsi, mainitsethan oGIIR-hankkeen seuraavan ohjeen mukaisesti:
"Työssä on käytetty aineistoja/ohjeita/laskentaresursseja, jotka on tarjonnut Suomen Akatemian rahoittama ‘Avoin paikkatiedon tutkimusinfrastruktuuri’ (oGIIR, urn:nbn:fi:research-infras-2016072513)”

**Laajennuksen on kehittänyt [Tatu Leppämäki](https://twitter.com/tadusk0) sekä Geoinformatiikan ja kartografian osasto Paikkatietokeskus FGI:ssä**

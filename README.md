# Tennis Doubles Elo Dashboard

A generalized version of Elo to track the results of our friendly tennis doubles games.

The dashboard is deployed on Heroku: https://aoullim-dashboard.herokuapp.com/

The Elo calculations are performed using [multielo](https://github.com/djcunningham0/multielo)
package. Follow that link to reach the GitHub page for the package, which includes
documentation and methodology for the generalized (multiplayer) Elo calculations.

brew install python3
pip install --upgrade pip
pip install -r requirements.txt
gunicorn -w 4 app:server

https://docs.gspread.org/en/latest/oauth2.html#enable-api-access
https://elements.heroku.com/buildpacks/buyersight/heroku-google-application-credentials-buildpack

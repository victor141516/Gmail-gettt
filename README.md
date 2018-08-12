## Endpoints

- `/`: Redirects to `/oauth2`
- `/oauth2`: Begins oauth proccess
- `/oauth2/callback`: Callback for oauth. Returns a unique uuid
- `/get?t={uuid}&n={nof_results[1]}&q={search_term}`: Returns [{},] of emails
- `/last?t={uuid}`: Returns the last email as HTML, just like in the Gmail website
- `/delete?t={uuid}`: Removes credentials from the database

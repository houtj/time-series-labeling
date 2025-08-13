

export const environment = {
	production: true,
	databaseUrl: window.location.hostname === 'localhost' ? 'http://localhost:8000' : '/api'
};

//ng build && firebase deploy --only hosting:hill-sequence

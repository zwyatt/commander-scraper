// When page is loaded, find all the decks and store them for later operations (ie. search, filter).
decks = document.querySelectorAll(".deck")
filter()

function fixAmp(text) {
	return text.replace(/&amp;/, "&");
}

// Filter by stock and search at the same time
function filter() {
	checked = document.querySelector('#stock').checked;
	term = document.querySelector('#deck-search').value.toLowerCase();
	term = fixAmp(term)
	for (deck of decks) {
		storeDecks = deck.querySelectorAll(".store-deck");
		numHidden = 0;

		for (storeDeck of storeDecks) {
			content = storeDeck.innerHTML.toLowerCase();
			content = fixAmp(content)
			if (checked
				&& content.includes("out")
				|| !content.includes(term)) {
				storeDeck.style.display = "none";
				numHidden++;
			} else {
				storeDeck.style.display = "";
			}
		}

		// If none of the store decks match, hide the entire deck
		if (numHidden == storeDecks.length) {
			deck.style.display = "none";
		} else {
			deck.style.display = "";
		}
	}
}
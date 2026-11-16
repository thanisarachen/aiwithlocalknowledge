const tripPrompts = {
  plan: `Please create a personalized Japan trip plan using my uploaded budget allocation, rough plan and travel reference documents.

Use the dates, flights, number of travelers, travel pace, preferences and spending limits in my documents. Ask about essential missing details instead of inventing them.

Focus on the itinerary, transportation, restaurants and activities. Do not include hotel recommendations or comparisons; I will use Compare hotels separately. Use a hotel already chosen in this chat, or clearly state area or station assumptions for travel estimates.

Include my requested day trips and wishlist where practical. Follow any requested spacing between day trips, group nearby places together, keep arrival day manageable and reserve enough time for airport transfers. Allow time for meals, cafe breaks and rest. Explain anything that cannot comfortably fit and suggest other places only when time allows.

Please provide:
1. A day-by-day itinerary with approximate times, transportation and meal suggestions.
2. Estimated spending and missing costs, respecting personal versus shared expenses and avoiding double counting.
3. Reservation checks and bad-weather alternatives.

Cite uploaded reference records or source links. Distinguish published facts, estimates and details needing confirmation. Keep currencies separate unless you state a verified exchange rate.`,

  hotels: `Using my uploaded rough plan, budget and hotel references, please compare 3 hotels for my trip.

Use my travel dates, number of travelers, room and bed requirements, walking pace and preferred distance from a station. Distinguish my personal hotel allowance from the whole-room total, and state any cost-sharing assumption. Ask about essential missing details.

For each hotel, explain:
- Room type, bed size and luggage space.
- Nearest station and usable entrance.
- Published walking distance or time, clearly marking anything unverified.
- Convenience for my wishlist, day trips and airport transfers.
- Advantages, disadvantages and any verified price information.

Recommend the best overall option and explain why. Do not invent rates or availability, or assume walking minutes prove an exact distance. Cite your sources. Please focus only on hotel comparison.`,

  budget: `Please review my uploaded trip budget against my stated spending target while preserving the requested buffer.

Please:
1. Check the original allocations and totals, distinguishing personal expenses from shared room or group costs.
2. Calculate any shortfall or amount left, counting the buffer only once.
3. Suggest specific changes and explain the trade-offs.
4. Show original and proposed amounts for changed categories, followed by revised expenses, buffer and total.
5. Identify missing costs and prices that need verification, including whether activity allowances match my rough plan.

Use the budget's stated currency. Keep other currencies separate unless you provide a verified exchange rate. Label proposed spending limits as budget caps, not confirmed prices. Ask about essential missing details and cite the relevant uploaded references. Please focus on the budget.`
};

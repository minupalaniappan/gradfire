CREATE TABLE textbooks_rentals (
  id SERIAL PRIMARY KEY,
  term_days int
);
CREATE TABLE textbooks_offers (
  book_id int REFERENCES courses_textbooks(id),
  merchant text,
  product_id text,
  rental_id int REFERENCES textbooks_rentals(id),
  list_price text,
  price_with_shipping text,
  updated timestamp
);
ALTER TABLE textbooks_offers ADD CONSTRAINT unique_offer UNIQUE (book_id, merchant, condition);
ALTER TABLE textbooks_offers DROP offer_id;
ALTER TABLE textbooks_offers DROP list_price;
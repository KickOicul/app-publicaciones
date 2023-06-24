CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    price DECIMAL(10, 2),
    image VARCHAR(255)
);

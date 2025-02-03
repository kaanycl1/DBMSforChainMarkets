CREATE TABLE Customer (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    total_spending INT DEFAULT 0
);

CREATE TABLE Transaction (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    product_id INT NOT NULL,
    branch_id INT NOT NULL,
    order_date DATE,
    amount INT DEFAULT 1,
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES Product(product_id) ON DELETE CASCADE,
    FOREIGN KEY (branch_id) REFERENCES MarketBranch(branch_id) ON DELETE CASCADE
);


CREATE TABLE Promotion (
    promotion_id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL,
    percentage INT DEFAULT 0,
    start_date DATE NOT NULL,
    end_date DATE,
    FOREIGN KEY (category_id) REFERENCES Category(category_id) ON DELETE CASCADE

);

CREATE TABLE Product (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50),
    price INT DEFAULT 0,
    category INT NOT NULL,
    lower_stock_alert INT DEFAULT 0,
    shelf_life INT NOT NULL,
    FOREIGN KEY (category) REFERENCES Category(category_id) ON DELETE CASCADE
);

CREATE TABLE Stock (
    stock_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    market_id INT NOT NULL,
    expiry_date DATE,
    amount INT DEFAULT 0,
    FOREIGN KEY (product_id) REFERENCES Product(product_id) ON DELETE CASCADE,
    FOREIGN KEY (market_id) REFERENCES MarketBranch(market_id) ON DELETE CASCADE
);

CREATE TABLE Category (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    parent_id INT,
    FOREIGN KEY (parent_id) REFERENCES Category(category_id) ON DELETE CASCADE
);

CREATE TABLE MarketBranch (
    market_id INT AUTO_INCREMENT PRIMARY KEY,
    budget INT,
    location VARCHAR(50)
);

CREATE TABLE Employee (
    employee_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50),
    branch INT,
    profession INT,
    manager INT,
    FOREIGN KEY (branch) REFERENCES MarketBranch(market_id) ON DELETE CASCADE,
    FOREIGN KEY (profession) REFERENCES Profession(profession_id) ON DELETE CASCADE,
    FOREIGN KEY (manager) REFERENCES Employee(employee_id)
);

CREATE TABLE Profession (
    profession_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50),
    salary INT DEFAULT 0
);
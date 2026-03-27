# 50 Test Queries for Conversational BI Agent

## Schema Reference
- **orders**: order_id, user_id, eval_set, order_number, order_dow, order_hour_of_day, days_since_prior_order
- **order_products_prior**: order_id, product_id, add_to_cart_order, reordered (~32M rows)
- **order_products_train**: order_id, product_id, add_to_cart_order, reordered (~1.4M rows)
- **products**: product_id, product_name, aisle_id, department_id
- **aisles**: aisle_id, aisle (134 rows)
- **departments**: department_id, department (21 rows)

---

## Category 1: Single-Table Simple Queries (Basics)

1. How many total orders are in the dataset?
2. How many unique users have placed orders?
3. What are all the department names?
4. List all aisles that contain the word "organic".
5. What is the average hour of the day when orders are placed?

## Category 2: Two-Table Joins

6. What are the top 10 most ordered products by name?
7. Which department has the most products?
8. How many products are in the "frozen" department?
9. Show the top 5 aisles with the highest number of products.
10. What are the 10 most reordered products? Show product names.

## Category 3: Three-Table Joins (Must-Have)

11. Which departments have the highest total number of orders?
12. What are the top 10 aisles by total order volume, along with their department?
13. Show the top 5 products in the "produce" department by order count.
14. What is the reorder rate for each department? Sort by highest reorder rate.
15. Which aisles in the "snacks" department have the most orders?

## Category 4: Four-Table Joins (Full Hierarchy)

16. For each department, show the top aisle and the top product in that aisle by order count.
17. What is the average cart position of products in each department?
18. Show the number of unique products ordered per department per aisle.
19. Which department-aisle combinations have the highest reorder rates?
20. List the top 3 products by order count for each of the top 5 departments.

## Category 5: Aggregation & Grouping

21. What is the distribution of orders by day of the week?
22. How many orders are placed each hour of the day?
23. What is the average number of products per order?
24. What is the average number of days between orders for repeat customers?
25. What is the distribution of order sizes (number of items per order)?

## Category 6: Filtering & Conditions

26. How many users have placed more than 50 orders?
27. What percentage of all product orders are reorders?
28. Which products are ordered most frequently as the first item added to cart?
29. Show all products that have never been reordered.
30. What are the most popular products ordered on weekends (Saturday=0, Sunday=1)?

## Category 7: Chart-Specific Queries (Visualization)

31. Show me a bar chart of orders by department.
32. Create a pie chart of the top 10 departments by order share.
33. Plot the number of orders by hour of the day as a line chart.
34. Show a bar chart comparing reorder rates across departments.
35. Visualize the distribution of days between orders as a histogram.

## Category 8: Multi-Step Reasoning (Stretch)

36. Show me which aisles have the highest reorder rate and how that correlates with average basket position.
37. What is the average basket size for users who order from the "produce" department vs those who don't?
38. Find the top 10 products that are most commonly bought together (appear in the same order most often).
39. Which users have the most diverse shopping baskets (highest number of unique departments per order on average)?
40. What is the relationship between order frequency (days_since_prior_order) and basket size?

## Category 9: Conversational Follow-Ups (Memory)

41. What are the top 5 departments by order count?
   → Follow-up: Now show only the dairy eggs department broken down by aisle.
42. Show me the most popular products.
   → Follow-up: Filter that to only products with "organic" in the name.
43. What is the reorder rate by department?
   → Follow-up: Now drill into the department with the highest reorder rate and show its top aisles.
44. How many orders are placed each day of the week?
   → Follow-up: Now show the average basket size for each day.

## Category 10: Error Recovery & Edge Cases

45. Show me the revenue by department. (There's no revenue/price column — agent should gracefully handle this)
46. What is the most popular product in the "electronics" department? (No electronics department exists)
47. Show me order trends over time. (No date column exists, only relative days_since_prior_order)
48. How many orders were placed in January 2024? (No absolute date data available)

## Category 11: Scale Handling (32M Row Table)

49. What is the total number of product-order pairs in the prior orders table?
50. Calculate the overall reorder rate across all 32 million rows in order_products_prior.

---

## Evaluation Scoring Guide

| Category | Queries | Tests |
|---|---|---|
| Basic SQL correctness | 1-5 | Single table, simple aggregates |
| Two-table joins | 6-10 | products + order_products |
| Three-table joins (Must-Have) | 11-15 | order_products + products + departments/aisles |
| Four-table joins | 16-20 | Full hierarchy traversal |
| Aggregation & grouping | 21-25 | GROUP BY, COUNT, AVG |
| Filtering & conditions | 26-30 | WHERE, HAVING, subqueries |
| Chart generation | 31-35 | Bar, pie, line, histogram |
| Multi-step reasoning | 36-40 | Complex analytics, correlation |
| Conversational memory | 41-44 | Follow-up references to prior results |
| Error recovery | 45-48 | Missing columns, invalid filters |
| Scale handling | 49-50 | 32M row performance |

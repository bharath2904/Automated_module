from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from datetime import datetime
import csv, os, re, time


def wait(ms):
    time.sleep(ms / 1000)


def parse_review_date(date_str):
    try:
        return datetime.strptime(date_str, "%B %d, %Y")
    except Exception:
        return None


def is_date_in_range(date, start, end):
    if date is None:
        return False
    if start and date < start:
        return False
    if end and date > end:
        return False
    return True


def click_show_more_until_2500(page, target_count=2500):
    last_count = 0
    attempts = 0
    max_attempts = 50

    while attempts < max_attempts:
        current_count = page.locator("p.Review-comment-bodyText").count()

        if current_count >= target_count:
            print(f"🎯 Reached target of {target_count} reviews.")
            break

        if current_count == last_count:
            print(f"⚠️ No new reviews loaded. Possibly end reached at {current_count}.")
            break

        last_count = current_count

        show_more_button = page.locator(
            "button.Review-paginator-button:not([disabled])"
        )
        if show_more_button.count() > 0:
            show_more_button.first.click()
            print(
                f"🔁 Clicked 'Show More Reviews' ({attempts + 1}) — Loaded: {current_count}"
            )
            wait(1000)
        else:
            print("🚫 'Show More Reviews' button not found or disabled.")
            break

        attempts += 1


def scrape_all_reviews(page, start_date=None, end_date=None):
    # First navigate to reviews section if not already there
    try:
        reviews_tab = page.locator(
            "a[data-element-name='review-score-and-count'], a:has-text('Reviews')"
        ).first
        if reviews_tab.count() > 0:
            reviews_tab.click()
            print("📝 Clicked on Reviews tab")
            page.wait_for_selector("p.Review-comment-bodyText", timeout=20000)
    except:
        print("⚠️ Couldn't find reviews tab, trying to proceed anyway")

    # Load more reviews with increased timeout
    click_show_more_until_2500(page)
    wait(2000)  # Increased wait time

    # Apply sorting if date range is specified
    if start_date or end_date:
        try:
            sort_by_dropdown = page.locator(
                "button[data-selenium='review-sort-dropdown-button']"
            ).first
            if sort_by_dropdown.count() > 0:
                sort_by_dropdown.click()
                time.sleep(2)  # Increased wait time
                most_recent_option = page.locator(
                    "li[data-selenium='review-sort-dropdown-option-most_recent']"
                ).first
                if most_recent_option.count() > 0:
                    most_recent_option.click()
                    print("🔽 Applied 'Most recent' review sorting")
                    page.wait_for_timeout(3000)  # Increased wait time
        except Exception as e:
            print(f"❌ Failed to apply 'Most recent' sort: {e}")

    # Extract all reviews with date filtering
    review_blocks = page.locator("div.Review-comment")
    review_dates = page.locator("div.Review-statusBar-left span")

    review_count = review_blocks.count()
    print(f"✅ Fetched {review_count} reviews in one go.")

    reviews = []
    failed_reviews = 0
    for i in range(review_count):
        try:
            # Increase timeout to 5 seconds and add retry logic
            block = review_blocks.nth(i)
            review_text = block.locator("p.Review-comment-bodyText").text_content(
                timeout=5000
            )

            review_date_raw = (
                review_dates.nth(i).text_content(timeout=2000)
                if i < review_dates.count()
                else ""
            )
            review_date = None

            # Try to get review text with retry
            for attempt in range(3):  # Retry up to 3 times
                try:
                    review_text = block.locator(
                        "p.Review-comment-bodyText"
                    ).text_content(timeout=5000)
                    break
                except Exception as e:
                    if attempt == 2:  # Last attempt failed
                        raise e
                    wait(1000)  # Wait 1 second before retry

            review_date_raw = ""
            for attempt in range(3):  # Retry up to 3 times
                try:
                    if i < review_dates.count():
                        review_date_raw = review_dates.nth(i).text_content(timeout=5000)
                    break
                except Exception as e:
                    if attempt == 2:  # Last attempt failed
                        raise e
                    wait(1000)  # Wait 1 second before retry

            review_date = None
            review_date_str = ""

            if review_date_raw:
                match = re.search(
                    r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}",
                    review_date_raw,
                )
                if match:
                    review_date_str = match.group(0)
                    review_date = parse_review_date(review_date_str)

            # Skip if date filtering is enabled and review is out of range
            if (start_date or end_date) and not is_date_in_range(
                review_date, start_date, end_date
            ):
                continue

            reviews.append(
                {
                    "review": review_text.strip(),
                    "review_date": review_date_str if review_date else "",
                }
            )

        except Exception as e:
            failed_reviews += 1
            print(f"⚠️ Failed to process review {i} after 3 attempts: {str(e)}")
            continue

    print(f"🏁 Finished scraping. Success: {len(reviews)}, Failed: {failed_reviews}")
    return reviews


def apply_star_rating_filter(page, star_rating):
    if star_rating == 0:
        return True

    filter_selectors = [
        f"label[data-element-name='search-filter-starratingwithluxury'][data-element-value='{star_rating}']",
        f"label[data-element-name='filter-star-rating'][data-element-value='{star_rating}']",
        f"label:has-text('{star_rating} star')",
    ]

    for selector in filter_selectors:
        if page.locator(selector).count() > 0:
            try:
                page.locator(selector).first.click()
                time.sleep(3)
                print(f"⭐ Applied {star_rating}-star filter")
                return True
            except Exception as e:
                print(f"⚠️ Failed to click star rating filter: {e}")
                continue

    print(f"❌ Could not find star rating filter for {star_rating} stars")
    return False


def get_hotel_results_page(context, city, timeout=15000):
    try:
        try:
            context.pages[0].wait_for_selector(
                "div[data-selenium='hotel-item']", timeout=5000
            )
            print("✅ Hotel results loaded on original page")
            return context.pages[0]
        except:
            pass

        if len(context.pages) > 1:
            for page in context.pages:
                try:
                    if "activities" not in page.url and "hotel" in page.url:
                        page.wait_for_selector(
                            "div[data-selenium='hotel-item']", timeout=5000
                        )
                        print(f"🌐 Found hotel results in new tab: {page.url}")
                        return page
                except:
                    continue

        print("⚠️ Couldn't find results quickly, trying fallback approach")
        for page in context.pages:
            try:
                if "search?city=" in page.url:
                    page.wait_for_selector(
                        "div[data-selenium='hotel-item']", timeout=5000
                    )
                    print(f"🔍 Found hotel results in page: {page.url}")
                    return page
            except:
                continue

        for page in reversed(context.pages):
            if "activities" not in page.url:
                return page

    except Exception as e:
        print(f"❌ Error finding hotel results page: {e}")

    return context.pages[0]


def scrape_reviews_from_agoda(
    city: str, star_rating: int, start_date=None, end_date=None
):
    sanitized_city = city.lower().replace(" ", "_")
    output_file = f"output/agoda_{sanitized_city}_hotel_reviews.csv"
    os.makedirs("output", exist_ok=True)

    parsed_start_date = (
        datetime.strptime(start_date, "%d-%m-%Y") if start_date else None
    )
    parsed_end_date = datetime.strptime(end_date, "%d-%m-%Y") if end_date else None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            # Optional: Set a user agent to mimic a real browser
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
        )
        page = context.new_page()

        print(f"🌍 Searching hotels in: {city}")
        page.goto("https://www.agoda.com", timeout=20000)

        try:
            print("Attempting to click cookie accept button...")
            page.locator("button#onetrust-accept-btn-handler").click(timeout=10000)
            print("✅ Cookie button clicked.")
        except Exception as e:
            print("⚠️ Cookie button not found or could not be clicked. Continuing...")
            pass

        # Input city and search - more reliable method
        search_input = page.locator(
            "input[placeholder*='destination'], input[placeholder*='property']"
        )
        search_input.fill(city)
        wait(2000)
        page.keyboard.press("ArrowDown")
        page.keyboard.press("Enter")
        wait(2000)

        try:
            search_button = page.locator("button[data-selenium='searchButton']").first
            if search_button.count() > 0:
                search_button.click()
        except:
            pass

        hotel_page = get_hotel_results_page(context, city)

        if not apply_star_rating_filter(hotel_page, star_rating):
            print("⚠️ Continuing without star rating filter")

        hotel_links = []
        hotel_ids = []
        page_num = 1

        while True:
            for _ in range(3):
                hotel_page.mouse.wheel(0, 1000)
                time.sleep(1)

            html = hotel_page.content()
            soup = BeautifulSoup(html, "html.parser")
            new_links = []
            new_ids = []

            # Find all hotel list items
            hotel_items = soup.select("li[data-hotelid]")
            for item in hotel_items:
                hotel_id = item.get("data-hotelid")
                card = item.select_one("a[href*='/hotel/']")
                if card:
                    href = card.get("href")
                    if href:
                        if not href.startswith("http"):
                            href = "https://www.agoda.com" + href
                        if href not in hotel_links:
                            hotel_links.append(href)
                            new_links.append(href)
                            hotel_ids.append(hotel_id)
                            new_ids.append(hotel_id)

            print(
                f"🔗 Page {page_num}: Found {len(new_links)} new hotels. Total: {len(hotel_links)}"
            )

            next_button = hotel_page.locator(
                "button:has-text('Next'), span:has-text('Next')"
            )
            if next_button.count() > 0:
                try:
                    next_button.first.click()
                    hotel_page.wait_for_timeout(3000)
                    page_num += 1
                except:
                    break
            else:
                break

        print(f"🏨 Total hotel links: {len(hotel_links)}")

        for i, link in enumerate(hotel_links[:5]):
            print(f"\n🔍 Hotel #{i+1} — {link}")
            hotel_page = context.new_page()
            try:
                hotel_page.goto(link, timeout=20000)
                time.sleep(3)

                reviews = scrape_all_reviews(
                    hotel_page, parsed_start_date, parsed_end_date
                )
                # Get hotel info
                name_element = hotel_page.locator(
                    "h1[data-selenium='hotel-header-name']"
                ).first
                hotel_name = (
                    name_element.text_content().strip()
                    if name_element.count() > 0
                    else f"Hotel #{i+1}"
                )

                rating_element = hotel_page.locator(
                    "span[data-element-name='mosaic-hotel-rating-container']"
                ).first
                hotel_rating = (
                    rating_element.text_content().strip()
                    if rating_element.count() > 0
                    else "N/A"
                )

                print(f"🏨 Hotel: {hotel_name}, Rating: {hotel_rating}")

                # Scrape reviews
                reviews = scrape_all_reviews(hotel_page)

                # Save to CSV
                if reviews:
                    file_exists = os.path.exists(output_file)
                    with open(output_file, "a", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(
                            f,
                            fieldnames=[
                                "city",
                                "hotel_name",
                                "hotel_id",
                                "rating",
                                "review",
                                "review_date",
                            ],
                        )
                        if not file_exists:
                            writer.writeheader()
                        writer.writerows(
                            [
                                {
                                    "city": city,
                                    "hotel_name": hotel_name,
                                    "hotel_id": hotel_ids[i],
                                    "rating": hotel_rating,
                                    "review": review["review"].strip(),
                                    "review_date": review["review_date"],
                                }
                                for review in reviews
                            ]
                        )
                    print(
                        f"✅ Saved {len(reviews)} reviews for '{hotel_name}' to '{output_file}'"
                    )
                else:
                    print(f"❌ No reviews found for '{hotel_name}'")

            except Exception as e:
                print(f"❌ Failed to process hotel #{i + 1}: {str(e)}")
                hotel_page.screenshot(path=f"error_hotel_{i+1}.png")
            finally:
                hotel_page.close()

        browser.close()
        print(f"\n🎉 Scraping complete. Output saved to: {output_file}")

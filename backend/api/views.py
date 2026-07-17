from django.db.models import Count, Prefetch, Min, Max
from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
import json

from comparison import PriceComparisonService
from comparison.substitute_ai import evaluate_substitute
from comparison.assistant_ai import parse_shopping_list, chat_with_assistant

from .models import ComparisonResult, SearchHistory, Platform, PriceAlert
from .serializers import (
    ProductSearchSerializer,
    SearchHistoryDetailSerializer,
    SearchHistoryListSerializer,
    ComparisonResultSerializer,
)

class ProductSearchView(APIView):
    def post(self, request):
        serializer = ProductSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            search = PriceComparisonService().search(
                serializer.validated_data["query"],
                lat=serializer.validated_data.get("lat"),
                lon=serializer.validated_data.get("lon"),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        output = SearchHistoryDetailSerializer(search)
        return Response(output.data, status=status.HTTP_201_CREATED)


class DeepComparisonView(APIView):
    def post(self, request):
        serializer = ProductSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            search = PriceComparisonService().deep_search(
                serializer.validated_data["query"],
                lat=serializer.validated_data.get("lat"),
                lon=serializer.validated_data.get("lon"),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        output = SearchHistoryDetailSerializer(search)
        return Response(output.data, status=status.HTTP_201_CREATED)


class ShoppingListParserView(APIView):
    def post(self, request):
        raw_text = request.data.get("text", "")
        if not raw_text:
            return Response({"detail": "Text is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        parsed_items = parse_shopping_list(raw_text)
        return Response({"items": parsed_items})


class ChatAssistantView(APIView):
    def post(self, request):
        messages = request.data.get("messages", [])
        context = request.data.get("context", {})
        
        if not messages:
            return Response({"detail": "Messages are required."}, status=status.HTTP_400_BAD_REQUEST)
            
        def generate():
            for chunk in chat_with_assistant(messages, context):
                # SSE format
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            yield "data: [DONE]\n\n"
            
        return StreamingHttpResponse(generate(), content_type="text/event-stream")


class CartOptimizerView(APIView):
    def post(self, request):
        items = request.data.get("items", [])
        strategy = request.data.get("strategy", "cheapest")
        lat = request.data.get("lat")
        lon = request.data.get("lon")
        
        if not items:
            return Response({"detail": "Items list is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            cart = PriceComparisonService().optimize_cart(items, strategy, lat, lon)
            return Response(cart)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SearchHistoryView(APIView):
    def get(self, request):
        queryset = (
            SearchHistory.objects.select_related("cheapest_platform")
            .annotate(result_count=Count("results"))
            .order_by("-created_at")
        )
        serializer = SearchHistoryListSerializer(queryset, many=True)
        return Response(serializer.data)


class ComparisonDetailView(APIView):
    def get(self, request, pk: int):
        try:
            search = (
                SearchHistory.objects.select_related("cheapest_platform")
                .prefetch_related(
                    Prefetch(
                        "results",
                        queryset=ComparisonResult.objects.select_related(
                            "platform", "product"
                        ).order_by("total_price", "delivery_charge", "price"),
                    )
                )
                .get(pk=pk)
            )
        except SearchHistory.DoesNotExist:
            return Response(
                {"detail": "Comparison not found."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = SearchHistoryDetailSerializer(search)
        return Response(serializer.data)


class SearchHistoryDeleteView(APIView):
    def delete(self, request, pk: int):
        deleted, _ = SearchHistory.objects.filter(pk=pk).delete()
        if deleted == 0:
            return Response(
                {"detail": "Search history item not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class AlertCreateView(APIView):
    def post(self, request):
        product_name = request.data.get("product_name")
        normalized_product_name = request.data.get("normalized_product_name")
        target_price = request.data.get("target_price")
        
        if not all([product_name, normalized_product_name, target_price]):
            return Response({"detail": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)
            
        alert, created = PriceAlert.objects.get_or_create(
            normalized_product_name=normalized_product_name,
            target_price=target_price,
            defaults={"product_name": product_name}
        )
        return Response({"detail": "Alert saved successfully", "id": alert.id})


class ProductHistoryView(APIView):
    def get(self, request, normalized_name: str):
        results = (
            ComparisonResult.objects.filter(
                normalized_product_name=normalized_name,
                total_price__isnull=False,
            )
            .select_related("platform")
            .order_by("created_at")
        )

        history_data = []
        for res in results:
            history_data.append({
                "date": res.created_at.isoformat(),
                "platform": res.platform.name if res.platform else "Unknown",
                "price": res.total_price,
            })

        return Response(history_data)

class ProductOffersView(APIView):
    def get(self, request, normalized_name: str):
        search_id = request.GET.get("search_id")
        
        # 1. Determine the search context
        search_results = []
        if search_id:
            try:
                search_history = SearchHistory.objects.get(pk=search_id)
                search_results = list(search_history.results.select_related("platform", "product").all())
            except SearchHistory.DoesNotExist:
                pass
                
        # Fallback to finding the most recent search that found this product
        if not search_results:
            latest_offer = ComparisonResult.objects.filter(
                normalized_product_name=normalized_name,
                total_price__isnull=False
            ).order_by("-created_at").first()
            
            if latest_offer and latest_offer.search_id:
                search_results = list(ComparisonResult.objects.filter(
                    search_id=latest_offer.search_id
                ).select_related("platform", "product").all())

        if not search_results:
            return Response({
                "product": None,
                "offers": [],
                "analytics": {},
                "platforms": []
            }, status=status.HTTP_404_NOT_FOUND)

        # 2. Map platforms and find the best offer per platform for this product
        platforms = Platform.objects.filter(is_active=True)
        
        product_info = None
        platform_offers = {}
        platform_errors = {}
        
        for res in search_results:
            if not res.platform:
                continue
            
            pid = res.platform.id
            
            if res.normalized_product_name == normalized_name and res.total_price is not None:
                if not product_info and res.product_name:
                    product_info = {
                        "name": res.product_name,
                        "brand": res.product.brand if res.product else "",
                        "quantity": res.quantity,
                        "image": res.raw_payload.get("image_url") or res.raw_payload.get("image") or ""
                    }
                    
                # Store the cheapest offer for this platform
                if pid not in platform_offers or res.total_price < platform_offers[pid].total_price:
                    platform_offers[pid] = res
            elif res.error_message:
                platform_errors[pid] = res.error_message

        # 3. Compute Analytics
        valid_offers = list(platform_offers.values())
        
        analytics = {}
        if valid_offers:
            prices = [float(o.total_price) for o in valid_offers]
            lowest_total = min(prices)
            highest_total = max(prices)
            avg_total = sum(prices) / len(prices)
            
            product_prices = [float(o.price) for o in valid_offers if o.price]
            lowest_product = min(product_prices) if product_prices else 0
            
            fastest_eta = None
            fastest_offer = None
            highest_discount = 0
            
            for o in valid_offers:
                # Check ETA
                eta_str = o.raw_payload.get("eta") or o.raw_payload.get("delivery_time")
                if eta_str:
                    try:
                        import re
                        nums = re.findall(r'\d+', str(eta_str))
                        if nums:
                            mins = int(nums[0])
                            if fastest_eta is None or mins < fastest_eta:
                                fastest_eta = mins
                                fastest_offer = o.platform.name
                    except Exception:
                        pass
                
                # Check Discount
                if o.price and o.raw_payload.get("mrp"):
                    try:
                        mrp = float(o.raw_payload["mrp"])
                        price = float(o.price)
                        if mrp > price:
                            discount = ((mrp - price) / mrp) * 100
                            if discount > highest_discount:
                                highest_discount = discount
                    except (ValueError, TypeError):
                        pass

            cheapest_offer = min(valid_offers, key=lambda o: o.total_price)

            analytics = {
                "lowest_product_price": lowest_product,
                "lowest_total_cost": lowest_total,
                "highest_price": highest_total,
                "average_price": avg_total,
                "money_saved": highest_total - lowest_total,
                "cheapest_provider": cheapest_offer.platform.name,
                "platforms_compared": len(valid_offers),
                "fastest_delivery": fastest_offer,
                "highest_discount": highest_discount
            }

        # 4. Build Platform Output
        platforms_output = []
        for p in platforms:
            p_data = {
                "platform": {
                    "id": p.id,
                    "name": p.name,
                    "logo_url": p.logo_url,
                    "brand_color": p.brand_color
                },
                "status": "not_available",
                "status_message": "Not Available",
                "offer": None
            }
            
            if p.id in platform_offers:
                p_data["status"] = "available"
                p_data["status_message"] = "Available"
                p_data["offer"] = ComparisonResultSerializer(platform_offers[p.id]).data
            elif p.id in platform_errors:
                err = str(platform_errors[p.id]).lower()
                if "unserviceable" in err or "location" in err or "zone" in err:
                    p_data["status"] = "not_serviceable"
                    p_data["status_message"] = "Unavailable in your location"
                else:
                    p_data["status"] = "error"
                    p_data["status_message"] = "Service temporarily unavailable"
            
            platforms_output.append(p_data)

        # 5. Find Substitutes
        similar_alternatives = []
        if product_info:
            other_products = {}
            for res in search_results:
                if res.normalized_product_name != normalized_name and res.product_name and res.total_price:
                    # Keep the cheapest offer for each distinct other product
                    pid = res.normalized_product_name
                    if pid not in other_products or res.total_price < other_products[pid]["price"]:
                        other_products[pid] = {
                            "normalized_id": pid,
                            "name": res.product_name,
                            "brand": res.product.brand if res.product else "",
                            "quantity": res.quantity,
                            "price": res.total_price,
                            "image": res.raw_payload.get("image_url") or res.raw_payload.get("image") or ""
                        }
            
            # Limit to top 5 distinct products to evaluate
            candidates = list(other_products.values())[:5]
            for cand in candidates:
                eval_result = evaluate_substitute(product_info["name"], cand["name"])
                if eval_result.get("comparable") and eval_result.get("score", 0.0) >= 0.70:
                    similar_alternatives.append({
                        "product": cand,
                        "evaluation": eval_result
                    })
            
            # Sort alternatives by score descending
            similar_alternatives.sort(key=lambda x: x["evaluation"].get("score", 0.0), reverse=True)

        if not valid_offers:
            return Response({
                "product": None,
                "offers": [],
                "analytics": {},
                "platforms": platforms_output,
                "similar_alternatives": similar_alternatives
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "product": product_info,
            "analytics": analytics,
            "platforms": platforms_output,
            "similar_alternatives": similar_alternatives
        })

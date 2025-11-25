"""Admin functionality related routes."""
from flask import Blueprint, request, jsonify, current_app, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Invoice
from utils.auth import admin_required
from utils.helpers import create_response, paginate_query
from datetime import datetime
from typing import Tuple

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin/users', methods=['GET'])
@jwt_required()
@admin_required
def get_users() -> Tuple[Response, int]:
    """
    Get user list (admin function).
    
    Returns:
        Tuple of (Flask response, status_code)
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        is_active = request.args.get('is_active', None)
        role = request.args.get('role', None, type=str)
        sort_by = request.args.get('sort_by', 'created_at', type=str)  # Sort field
        sort_order = request.args.get('sort_order', 'desc', type=str)  # Sort direction
        
        # Limit maximum items per page
        per_page = min(per_page, 100)
        
        # Import necessary functions
        from sqlalchemy import func, case
        
        # Build query including invoice count
        query = db.session.query(
            User,
            func.count(Invoice.id).label('invoice_count')
        ).outerjoin(Invoice, User.id == Invoice.user_id)
        
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            query = query.filter(User.is_active == is_active_bool)
        
        if role:
            query = query.filter(User.role == role)
        
        # Group by user
        query = query.group_by(User.id)
        
        # Handle sorting
        if sort_by == 'invoice_count':
            if sort_order.lower() == 'asc':
                query = query.order_by(func.count(Invoice.id).asc())
            else:
                query = query.order_by(func.count(Invoice.id).desc())
        elif sort_by == 'username':
            if sort_order.lower() == 'asc':
                query = query.order_by(User.username.asc())
            else:
                query = query.order_by(User.username.desc())
        elif sort_by == 'email':
            if sort_order.lower() == 'asc':
                query = query.order_by(User.email.asc())
            else:
                query = query.order_by(User.email.desc())
        elif sort_by == 'created_at':
            if sort_order.lower() == 'asc':
                query = query.order_by(User.created_at.asc())
            else:
                query = query.order_by(User.created_at.desc())
        else:
            # Default to descending order by creation time
            query = query.order_by(User.created_at.desc())
        
        # Get total count (must calculate before grouping)
        # Build base query for counting first
        count_query = User.query
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            count_query = count_query.filter(User.is_active == is_active_bool)
        if role:
            count_query = count_query.filter(User.role == role)
        total = count_query.count()
        
        # Pagination
        offset = (page - 1) * per_page
        users_with_counts = query.offset(offset).limit(per_page).all()
        
        # Build response data
        items = []
        for user, invoice_count in users_with_counts:
            user_dict = user.to_dict()
            user_dict['invoice_count'] = invoice_count or 0
            items.append(user_dict)
        
        # Calculate pagination info
        pages = (total + per_page - 1) // per_page if total > 0 else 0
        has_prev = page > 1
        has_next = page < pages
        
        result = {
            'items': items,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': pages,
                'has_prev': has_prev,
                'has_next': has_next,
                'prev_num': page - 1 if has_prev else None,
                'next_num': page + 1 if has_next else None
            }
        }
        
        return create_response(
            'Users retrieved successfully',
            data=result,
            status_code=200
        )
        
    except Exception as e:
        current_app.logger.error(f'Get users error: {str(e)}')
        return create_response(
            'Failed to retrieve users',
            error='server_error',
            status_code=500
        )


@admin_bp.route('/admin/users/<int:user_id>/toggle', methods=['PUT'])
@jwt_required()
@admin_required
def toggle_user_status(user_id: int) -> Tuple[Response, int]:
    """
    Enable/disable user (admin function).
    
    Args:
        user_id: User ID
    
    Returns:
        Tuple of (Flask response, status_code)
    """
    try:
        user = db.session.get(User, user_id)
        
        if not user:
            return create_response(
                'User not found',
                error='user_not_found',
                status_code=404
            )
        
        # Cannot disable own account
        current_user_id = int(get_jwt_identity())
        if user.id == current_user_id:
            return create_response(
                'Cannot disable your own account',
                error='invalid_operation',
                status_code=400
            )
        
        # Toggle status
        user.is_active = not user.is_active
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return create_response(
            f'User {"enabled" if user.is_active else "disabled"} successfully',
            data={'user': user.to_dict()},
            status_code=200
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Toggle user status error: {str(e)}')
        return create_response(
            'Failed to toggle user status',
            error='server_error',
            status_code=500
        )


@admin_bp.route('/admin/stats', methods=['GET'])
@jwt_required()
@admin_required
def get_stats() -> Tuple[Response, int]:
    """
    Get system statistics (admin function).
    
    Returns:
        Tuple of (Flask response, status_code)
    """
    try:
        # User statistics
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        admin_users = User.query.filter_by(role='admin').count()
        
        # Invoice statistics
        from sqlalchemy import func
        total_invoices = Invoice.query.count()
        invoices_by_status = {}
        statuses = db.session.query(Invoice.status, func.count(Invoice.id)).group_by(Invoice.status).all()
        for status, count in statuses:
            invoices_by_status[status] = count
        
        # Invoice statistics for last 7 days
        from datetime import timedelta
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_invoices = Invoice.query.filter(Invoice.created_at >= seven_days_ago).count()
        
        stats = {
            'users': {
                'total': total_users,
                'active': active_users,
                'admin': admin_users,
                'regular': total_users - admin_users
            },
            'invoices': {
                'total': total_invoices,
                'by_status': invoices_by_status,
                'recent_7_days': recent_invoices
            }
        }
        
        return create_response(
            'Statistics retrieved successfully',
            data=stats,
            status_code=200
        )
        
    except Exception as e:
        current_app.logger.error(f'Get stats error: {str(e)}')
        return create_response(
            'Failed to retrieve statistics',
            error='server_error',
            status_code=500
        )


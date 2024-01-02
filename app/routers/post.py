from fastapi import status, HTTPException, Depends, APIRouter, Response, Query
from typing import Annotated
from sqlalchemy.orm import Session
from .. import utils
from .. import models, schemas, oauth2
from ..database import get_db, engine
from sqlalchemy import func




router = APIRouter(
    prefix="/posts",
    tags=["posts"]
    )

@router.get("/", response_model=list[schemas.PostOut])
async def get_posts(db:Session = Depends(get_db),
                    current_user: schemas.TokenData = Depends(oauth2.get_current_user),
                    limit: int = 10,
                    skip: int = 0,
                    search: Annotated[str | None, Query(max_length=50)] = ""):

    results = db.query(models.Post, func.count(models.Vote.post_id).label("votes")).join(
        models.Vote, models.Vote.post_id==models.Post.id, isouter=True).group_by(models.Post.id).filter(
        models.Post.title.contains(search)).limit(limit=limit).offset(skip).all()

    return results

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.Post)
async def create_posts(post: schemas.PostCreate, 
                       db: Session = Depends(get_db), 
                       current_user: schemas.TokenData = Depends(oauth2.get_current_user)):
    
    new_post = models.Post(owner_id=current_user.id, **post.model_dump())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post

@router.get("/{id}", response_model=schemas.PostOut)
async def get_post(id: int, 
                   db: Session = Depends(get_db), 
                   current_user: schemas.TokenData = Depends(oauth2.get_current_user)):
    
    post = db.query(models.Post, func.count(models.Vote.post_id).label("votes")).join(
        models.Vote, models.Vote.post_id==models.Post.id, isouter=True).group_by(models.Post.id).first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with id: {id} was not found")
    return post

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def get_post(id: int, 
                   db: Session = Depends(get_db), 
                   current_user: schemas.TokenData = Depends(oauth2.get_current_user)):
    
    post_query = db.query(models.Post).filter(models.Post.id==id)
    post = post_query.first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with id: {id} was not found")
    
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to perform requested action")
    
    post_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{id}", response_model=schemas.Post)
def update_post(id: int,
                updated_post: schemas.PostCreate, 
                db: Session = Depends(get_db), 
                current_user: schemas.TokenData = Depends(oauth2.get_current_user)):
    
    post_query = db.query(models.Post).filter(models.Post.id==id)
    post = post_query.first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with id: {id} was not found")
    
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to perform requested action")

    post_query.update(updated_post.model_dump(), synchronize_session=False)
    db.commit()
    return post
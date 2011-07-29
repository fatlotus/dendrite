//
//  BlockingTestHelper.h
//  DendriteClient
//
//  Created by Jeremy Archer on 7/29/11.
//  Copyright 2011 University of Chicago CI. All rights reserved.
//

#import <SenTestingKit/SenTestingKit.h>
#import <Foundation/Foundation.h>

@interface BlockingTestHelper : NSObject {
    NSMutableDictionary * firedEvents;
}

- (void)waitForEvent:(NSString*)event;
- (void)triggerEvent:(NSString*)event;

@property(nonatomic, readwrite, assign) NSUInteger timeout;
@end

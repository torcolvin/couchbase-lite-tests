//
//  UpdateDatabase.swift
//  CBL-Tests-iOS
//
//  Created by Callum Birks on 08/08/2023.
//

import Vapor
import CouchbaseLiteSwift

extension Handlers {
    static let updateDatabase : EndpointHandlerEmptyResponse = { req throws in
        guard let updateRequest = try? req.content.decode(ContentTypes.UpdateRequest.self)
        else {
            throw TestServerError.badRequest("Request body is not a valid Update request.")
        }

        for update in updateRequest.updates {
            switch(update.type) {
            case .UPDATE:
                try DocumentUpdater.processUpdate(item: update, inDB: updateRequest.database)
            case .DELETE:
                guard let collection = try DatabaseManager.shared?.collection(update.collection, inDB: updateRequest.database)
                else {
                    throw TestServerError(domain: .CBL, code: CBLError.notFound, message: "Collection not found")
                }
                guard let doc = try? collection.document(id: update.documentID)
                else {
                    throw TestServerError(domain: .CBL, code: CBLError.notFound, message: "Document not found")
                }
                try? collection.delete(document: doc)
            case .PURGE:
                guard let collection = try DatabaseManager.shared?.collection(update.collection, inDB: updateRequest.database)
                else {
                    throw TestServerError(domain: .CBL, code: CBLError.notFound, message: "Collection not found")
                }
                guard let doc = try? collection.document(id: update.documentID)
                else {
                    throw TestServerError(domain: .CBL, code: CBLError.notFound, message: "Document not found")
                }
                try? collection.purge(document: doc)
            }
        }
        
        return Response(status: .ok)
    }
}

